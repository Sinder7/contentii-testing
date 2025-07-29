import logging
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
logging.basicConfig(filename="parser.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

@dataclass
class Config:
    base_url: str
    login_url: str
    username: str
    password: str
    server: str
    target: str
    headers: dict
    db: str
    table: str


def pretty_print_dict(data: dict) -> None:
    """
    Выводит данные из словаря в ввиде таблицы в терминал
    """

    with_key = max(len(k) for k in data)
    with_value = max(len(v) for v in data.values())

    print(f"{'ID'.ljust(with_key)} | {'Name'.ljust(with_value)}")
    print(f"{'-'*with_key} | {'-'*with_value}")

    for k, v in data.items():
        print(f"{k.ljust(with_key)} | {v.ljust(with_value)}")


class PhpMyAdminClient:
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)

    def login(self) -> None:
        resp = self.session.get(self.config.base_url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", {"name": "login_form"})
        if not form:
            logger.error("Не найдена форма логина")
            return

        payload = {
            input["name"]: input.get("value", "")
            for input in form.select("input[type=hidden]")
        }
        payload.update({
            "pma_username": self.config.username,
            "pma_password": self.config.password,
            "server": self.config.server,
            "target": self.config.target,
        })

        post = self.session.post(
            self.config.login_url,
            data=payload,
            headers={"Referer": resp.url},
        )
        post.raise_for_status()
        if "Invalid login" in post.text:
            logger.error("Неверный логин/пароль")
        logger.info("Аунтентификая пройдена")

    def fetch_data_in_table(self) -> dict[str, str]:
        logger.info("Получение данныз из таблицы...")
        url = (
            f"{self.config.base_url}index.php?"
            f"route=/sql&server={self.config.server}"
            f"&db={self.config.db}&table={self.config.table}"
        )
        resp = self.session.get(url, headers={"Referer": self.config.login_url})
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        mapping: dict[str, str] = {}
        for i in soup.select("tbody tr"):
            tds = i.find_all("td")
            key = tds[4].get_text(strip=True)
            value = tds[5].get_text(strip=True)
            mapping[key] = value
        return mapping


def main():
    logger.info("Запуск приложения")
    config = Config(
        base_url="http://185.244.219.162/phpmyadmin/",
        login_url="http://185.244.219.162/phpmyadmin/index.php?route=/",
        username="test",
        password="JHFBdsyf2eg8*",
        server="1",
        target="index.php",
        headers={"User-Agent": "Mozilla/5.0"},
        db="testDB",
        table="users"
    )

    client = PhpMyAdminClient(config)
    try:
        client.login()
        results = client.fetch_data_in_table()
        pretty_print_dict(data=results)
        logger.info("Данные успешно получены и выведены в терминал")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == "__main__":
    main()