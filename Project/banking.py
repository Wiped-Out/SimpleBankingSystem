#!/usr/bin/env python3
from random import randint
import sqlite3
from typing import Callable, Optional, Tuple


class BankingSystem:
    def __init__(self) -> None:
        self.database()

    class Login:
        """Asks for credentials to the user before letting him access to sensitive info."""

        def __init__(self, f: Callable[['BankingSystem', str], None]) -> None:
            self.f = f

        def __call__(self):
            card = input('Enter your card number:\n')
            PIN: str = input('Enter your PIN:\n')
            if BankingSystem.check_credentials(card, PIN):
                print('You have successfully logged in!\n')
                self.f(BankingSystem, card, PIN)
                print('You have successfully logged out.\n')
                return
            else:
                print('Wrong card number or PIN\n')

    def menu(self) -> None:
        """Main driver of the program."""
        while True:
            print("1. Create an account\n2. Log into account\n0. Exit")
            choice: str = input()
            if choice == '1':
                self.create_account()
            elif choice == '2':
                self.account()
            elif choice == '0':
                print('Bye!')
                exit()
            else:
                print('Unknown option.')

    @staticmethod
    def database(
        card: Optional[str] = None,
        pin: Optional[str] = None,
        balance: Optional[int] = None,
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
                INSERT OR IGNORE INTO card (number, pin, balance)
                VALUES (?, ?, ?);
                ''',
                    (card, pin, balance),
                )

    @staticmethod
    def check_credentials(card: str, pin: str) -> bool:
        """Gets the credentials of a card on a db"""
        with sqlite3.connect('card.s3db') as data:
            cursor = data.cursor()
            cursor.execute(
                '''
            SELECT pin FROM card WHERE number = (?) and pin = (?);
            ''',
                (card, pin),
            )
            result = cursor.fetchone()
            return bool(result)

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
        """Generates numbers until it passes the Luhn algorithm"""
        while True:
            random_card = ''.join(['400000'] + [str(randint(0, 9)) for _ in range(11)])
            random_PIN = ''.join([str(randint(0, 9)) for _ in range(4)])
            if not BankingSystem.check_credentials(random_card, random_PIN):
                if BankingSystem.luhn_algorithm(random_card):
                    return random_card, random_PIN
            else:
                continue

    def create_account(self) -> None:
        card, PIN = self.generate_numbers()
        self.database(card, PIN, 0)
        print('\nYour card has been created')
        print(f'Your card number:\n{card}')
        print(f'Your card PIN:\n{PIN}\n')

    @staticmethod
    def get_update(
        From: Optional[str] = None,
        to: Optional[str] = None,
        amount: Optional[int] = None,
        close: Optional[bool] = False,
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
            elif From and amount:
                cur.execute(
                    '''
                UPDATE card SET balance = (balance + ?) WHERE number LIKE (?);
                ''',
                    (amount, From),
                )
                return 'Income was added!'
            elif close:
                cur.execute(
                    '''
                DELETE FROM card where number = (?);
                ''',
                    (From,),
                )
            else:
                cur.execute(
                    '''SELECT balance FROM card WHERE number LIKE (?);''', (From,)
                )
                return cur.fetchone()[0]
        return 'Error.'

    @Login
    def account(self, card: Optional[str] = None, pin: Optional[str] = None) -> None:
        while True:
            print(
                '1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit'
            )
            choice: str = input()
            if choice == '1':
                print(f"\nBalance: {self.get_update(card)}\n")
            elif choice == '2':
                income: int = int(input('Enter income:\n'))
                print(self.get_update(From=card, amount=income))
            elif choice == '3':
                to: str = input('Enter card number:\n')
                if card == to:
                    print('You can\'t transfer money to the same account!\n')
                elif not self.luhn_algorithm(to):
                    print(
                        'You probably made a mistake in the card number. Please try again!\n'
                    )
                elif not self.check_credentials(to):
                    print('Such card does not exist.\n')
                else:
                    amount: int = int(
                        input('Enter how much money you want to transfer:\n')
                    )
                    if amount > int(self.get_update(card)):
                        print('Not enough money!\n')
                        continue
                    print(self.get_update(card, to, amount))
            elif choice == '4':
                self.get_update(From=card, close=True)
                return
            elif choice == '5':
                return
            elif choice == '0':
                print('Bye!')
                exit()
            else:
                print('Unknown option.\n')


if __name__ == '__main__':
    System = BankingSystem()
    System.menu()
