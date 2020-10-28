#!/usr/bin/env python3
import sqlite3
from contextlib import contextmanager
from random import randint
from sqlite3.dbapi2 import Cursor
from typing import Any, Generator, Tuple


class Bank:
    def __init__(self) -> None:
        self.cursor()

    @staticmethod
    @contextmanager
    def cursor() -> Generator[Cursor, Any, Any]:
        """Creates the db and yields a cursor."""
        with sqlite3.connect('card.s3db') as data:
            data.executescript(
                '''
                CREATE TABLE IF NOT EXISTS card (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                number TEXT NOT NULL UNIQUE,
                pin TEXT NOT NULL,
                balance INTEGER DEFAULT 0 NOT NULL
                );
                '''
            )
        with sqlite3.connect('card.s3db') as db:
            yield db.cursor()

    def menu(self) -> None:
        """Main driver of the program."""
        while True:
            print("1. Create an account\n2. Log into account\n0. Exit")
            choice: str = input()
            if choice == '1':
                self.create_account()
            elif choice == '2':
                card = input('Enter your card number:\n')
                PIN = input('Enter your PIN:\n')
                if not self.check_credentials(card, PIN):
                    print('Wrong card number or PIN.\n')
                    continue
                with Account(card) as acc:
                    acc.menu()
            elif choice == '0':
                raise SystemExit('Bye!')
            else:
                print('Unknown option.')

    @staticmethod
    def check_credentials(card: str, pin: str) -> bool:
        """Gets the credentials of a card from the db"""
        with Bank.cursor() as cur:
            cur.execute(
                ' SELECT pin FROM card WHERE number = (?) AND pin = (?);', (card, pin)
            )
            return bool(cur.fetchone())

    @staticmethod
    def luhn_algorithm(card_number: str) -> bool:
        number = [int(i) for i in card_number]
        for x, num in enumerate(number, 1):
            if x % 2 == 0:
                continue
            n = num * 2
            number[x - 1] = n if n < 10 else n - 9
        return sum(number) % 10 == 0

    @staticmethod
    def generate_numbers() -> Tuple[str, str]:
        """Generates numbers until it passes Luhn's algorithm"""
        while True:
            random_card = ''.join(['400000'] + [str(randint(0, 9)) for _ in range(11)])
            random_PIN = ''.join([str(randint(0, 9)) for _ in range(4)])
            if Bank.luhn_algorithm(random_card):
                return random_card, random_PIN
            else:
                continue

    def create_account(self) -> None:
        card, PIN = self.generate_numbers()
        with self.cursor() as cur:
            cur.execute(
                'INSERT OR IGNORE INTO card (number, pin)VALUES (?, ?);', (card, PIN)
            )
        print('\nYour card has been created')
        print(f'Your card number:\n{card}')
        print(f'Your card PIN:\n{PIN}\n')

    @staticmethod
    def transfer(to: str, amount: int) -> str:
        with Bank.cursor() as cur:
            cur.execute(
                '''
                UPDATE card SET balance = (balance + ?) WHERE number LIKE (?);
                ''',
                (amount, to),
            )
            return 'Success!'


class Account:
    def __init__(self, card: str) -> None:
        self.card = card

    @staticmethod
    def exists(card: str) -> bool:
        with Bank.cursor() as cur:
            cur.execute('SELECT number FROM card WHERE number = (?);', (card,))
            return bool(cur.fetchone())

    @property
    def balance(self) -> int:
        with Bank.cursor() as cur:
            return cur.execute(
                'SELECT balance FROM card WHERE number = (?);', (self.card,)
            ).fetchone()[0]

    @balance.setter
    def balance(self, balance: int) -> None:
        with Bank.cursor() as cur:
            cur.execute(
                'UPDATE card SET balance = (balance + ?) WHERE number = (?);',
                (balance, self.card),
            )

    def close_account(self) -> None:
        with Bank.cursor() as cur:
            cur.execute('DELETE FROM card WHERE number = (?);', (self.card,))

    def menu(self) -> None:
        while True:
            print(
                '1. Balance\n'
                '2. Add income\n'
                '3. Do transfer\n'
                '4. Close Account\n'
                '5. Log out\n'
                '0. Exit'
            )
            choice: str = input()
            if choice not in ('1', '2', '3', '4', '5', '0'):
                print('Unknown option.')
                continue
            elif choice == '1':
                print(f"Balance: {self.balance}\n")
            elif choice == '2':
                income: int = int(input('Enter income:\n'))
                self.balance = income
                print('Income was added!')
            elif choice == '3':
                to: str = input('Enter card number:\n')
                if self.card == to:
                    print('You can\'t transfer money to the same account!\n')
                elif not Bank.luhn_algorithm(to):
                    print(
                        'You probably made a mistake in the card number. Please try again!\n'
                    )
                elif not self.exists(to):
                    print('Such card does not exist.\n')
                else:
                    amount = int(input('Enter how much money you want to transfer:\n'))
                    if amount > self.balance:
                        print('Not enough money!\n')
                        continue
                    self.balance = -amount  # take 'amount' from the account balance.
                    print(Bank.transfer(to, amount))
            elif choice == '4':
                self.close_account()
                return
            elif choice == '5':
                raise Exception('You have successfully logged out.')
            elif choice == '0':
                raise SystemExit('Bye!')

    def __enter__(self):
        print('You have successfully logged in!\n')
        return self

    def __exit__(self, exc_type: type, value: str, traceback):
        if exc_type is SystemExit:
            raise SystemExit(value)
        if exc_type:
            print(value)
            return True


if __name__ == '__main__':
    System = Bank()
    System.menu()
