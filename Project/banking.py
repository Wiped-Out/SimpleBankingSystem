#!/usr/bin/env python3
from random import randint
import sqlite3
from typing import Optional, Tuple


class BankingSystem:
    def __init__(self) -> None:
        self.database()

    def menu(self) -> None:
        """Main driver of the program."""
        while True:
            print("1. Create an account\n2. Log into account\n0. Exit")
            choice: str = input()
            if choice == '1':
                self.create_account()
            elif choice == '2':
                card = input('Enter your card number:\n')
                PIN: str = input('Enter your PIN:\n')
                try:
                    with Account(card, PIN) as acc:
                        acc.menu()
                except ValueError as e:  # Will catch the exception raised when the card number or PIN is wrong and will print the msg.
                    print(e)
            elif choice == '0':
                print('Bye!')
                exit()
            else:
                print('Unknown option.')

    @staticmethod
    def database(
        card: Optional[str] = None,
        pin: Optional[str] = None,
    ) -> None:
        """Creates a db if no parameters are provided, else creates account."""
        with sqlite3.connect('card.s3db') as data:
            if not card:
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
            else:
                cursor = data.cursor()
                cursor.execute(
                    '''
                INSERT OR IGNORE INTO card (number, pin)
                VALUES (?, ?, ?);
                ''',
                    (card, pin),
                )

    @staticmethod
    def check_credentials(card: str, pin: str) -> bool:
        """Gets the credentials of a card from the db"""
        with sqlite3.connect('card.s3db') as data:
            cursor = data.cursor()
            cursor.execute(
                '''
            SELECT pin FROM card WHERE number = (?) AND pin = (?);
            ''',
                (card, pin),
            )
            return bool(cursor.fetchone())

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
            if BankingSystem.luhn_algorithm(random_card):
                return random_card, random_PIN
            else:
                continue

    def create_account(self) -> None:
        card, PIN = self.generate_numbers()
        self.database(card, PIN)
        print('\nYour card has been created')
        print(f'Your card number:\n{card}')
        print(f'Your card PIN:\n{PIN}\n')

    @staticmethod
    def get_update(
        From: Optional[str] = None,
        to: Optional[str] = None,
        amount: Optional[int] = None,
    ) -> str:
        """Gets, updates and deletes entries from the database"""
        with sqlite3.connect('card.s3db') as data:
            cur = data.cursor()
            if From and to:
                cur.execute(
                    '''
                UPDATE card SET balance = (balance + ?) WHERE number LIKE (?);
                ''',
                    (amount, to),
                )
                cur.execute(
                    '''
                UPDATE card SET balance = (balance - ?) WHERE number LIKE (?);
                ''',
                    (amount, From),
                )
                return 'Success!'
        return 'Error.'


class Account:
    __slots__ = ('card', 'pin', 'db')

    def __init__(self, card: str, pin: str) -> None:
        self.card, self.pin = card, pin
        self.db = sqlite3.connect('card.s3db').cursor()

    def exists(self, card: str) -> bool:
        self.db.execute('SELECT number FROM card WHERE number = (?);', (card,))
        return bool(self.db.fetchone())

    def balance(self) -> int:
        self.db.execute('SELECT balance FROM card WHERE number = (?);', (self.card,))
        return self.db.fetchone()[0]

    def add_balance(self, balance: int) -> str:
        self.db.execute(
            'UPDATE card SET balance = (balance + ?) WHERE number = (?);',
            (balance, self.card),
        )
        return 'Income was added!'

    def close_account(self) -> None:
        self.db.execute('DELETE FROM card WHERE number = (?);', (self.card,))

    def menu(self) -> None:
        options = {
            '1': 'Balance',
            '2': 'Add income',
            '3': 'Do transfer',
            '4': 'Close Account',
            '5': 'Log out',
            '0': 'Exit',
        }
        while True:
            for k, v in options.items():
                print(f'{k}. {v}')
            choice: str = input()
            if choice not in options:
                print('Unknown option.')
                continue
            elif choice == '1':
                print(f"\nBalance: {self.balance()}\n")
            elif choice == '2':
                income: int = int(input('Enter income:\n'))
                print(self.add_balance(income))
            elif choice == '3':
                to: str = input('Enter card number:\n')
                if self.card == to:
                    print('You can\'t transfer money to the same account!\n')
                elif not BankingSystem.luhn_algorithm(to):
                    print(
                        'You probably made a mistake in the card number. Please try again!\n'
                    )
                elif not self.exists(to):
                    print('Such card does not exist.\n')
                else:
                    amount: int = int(
                        input('Enter how much money you want to transfer:\n')
                    )
                    if amount > int(self.balance()):
                        print('Not enough money!\n')
                        continue
                    print(BankingSystem.get_update(self.card, to, amount))
            elif choice == '4':
                self.close_account()
                return
            elif choice == '5':
                raise Exception('You have successfully logged out.')
            elif choice == '0':
                raise SystemExit('Bye!')

    def __enter__(self):
        if not BankingSystem.check_credentials(self.card, self.pin):
            raise ValueError('Wrong card number or PIN.\n')
        print('You have successfully logged in!\n')
        return self

    def __exit__(self, type, value, traceback):
        self.db.close()
        if type == SystemExit:
            raise SystemExit(value)
        if type:
            print(value)
            return True


if __name__ == '__main__':
    System = BankingSystem()
    System.menu()
