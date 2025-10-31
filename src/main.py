#!/usr/bin/env python
import argparse
from lib.tg_bot import TgBot
from lib.envdefault import EnvDefault

def main() -> None:
    parser = argparse.ArgumentParser(description="Runtime parameters",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--redis_host', action=EnvDefault, envvar='REDIS_HOST', help='Redis server host name')
    parser.add_argument('--redis_port', action=EnvDefault, envvar='REDIS_PORT', help='Redis server port number')
    parser.add_argument('--redis_password', action=EnvDefault, envvar='REDIS_PASSWORD', help='Redis server password')
    parser.add_argument('-gsa', '--gsa_file',            action=EnvDefault, envvar='GSA_FILE',       help='Path to google service account file')
    parser.add_argument('-tg_token', '--telegram_token', action=EnvDefault, envvar='TELEGRAM_TOKEN', help='Telegram token', required=True)

    args = parser.parse_args()
    config = vars(args)

    bot = TgBot(config['telegram_token'], config)
    bot.run()

if __name__ == "__main__":
    main()