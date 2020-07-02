#!/usr/bin/env python3
from random import sample
import sqlite3


class BankingSystem:

    def __init__(self):
        self.database()

    def menu(self) -> None:
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
    def database(card=None, pin=None, balance=None) -> None:
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

    def _login(f):
        def wrapper(*args, **kwargs):
            try:
                card: str = input('Enter your card number:\n')
                PIN: str = input('Enter your PIN:\n')
                if BankingSystem.check_credentials(card)[0] == PIN:
                    print('You have successfully logged in!\n')
                    return f(*args, **kwargs, card=card)
                else:
                    print('Wrong card number or PIN\n')
            except TypeError:
                print('Wrong card number or PIN\n')
        return wrapper

    @staticmethod
    def check_credentials(card) -> str:
        with sqlite3.connect('card.s3db') as data:
            cursor = data.cursor()
            cursor.execute(
                '''
            SELECT pin FROM card WHERE number LIKE (?);
            ''',
                (card,),
            )
            return cursor.fetchone()

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
    def generate_numbers() -> tuple:
        while True:
            random_card = ''.join(
                ['400000'] + [str(n) for n in sample(range(9), 9)] + ['7']
            )
            random_PIN = ''.join([str(n) for n in sample(range(9), 4)])
            if not BankingSystem.check_credentials(random_card):
                if BankingSystem.luhn_algorithm(random_card):
                    yield [random_card, random_PIN]
            else:
                continue

    def create_account(self) -> None:
        card, PIN = next(self.generate_numbers())
        self.database(card, PIN, 0)
        print('\nYour card has been created')
        print(f'Your card number:\n{card}')
        print(f'Your card PIN:\n{PIN}\n')

    @staticmethod
    def get_update(From=None, to=None, amount=None, close=False) -> str:
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

    @_login
    def account(self, card=None) -> None:
        while True:
            print(
                '1. Balance\n2. Add income\n3. Do transfer\n4. Close account\n5. Log out\n0. Exit'
            )
            choice: str = input()
            if choice == '1':
                print(f"\nBalance: {self.get_update(card)}\n")
            elif choice == '2':
                income = int(input('Enter income:\n'))
                print(self.get_update(From=card, amount=income))
            elif choice == '3':
                to = input('Enter card number:\n')
                if card == to:
                    print('You can\'t transfer money to the same account!\n')
                elif not self.luhn_algorithm(to):
                    print(
                        'You probably made a mistake in the card number. Please try again!\n'
                    )
                elif not self.check_credentials(to):
                    print('Such card does not exist.\n')
                else:
                    amount: str = input('Enter how much money you want to transfer:\n')
                    if int(amount) > self.get_update(card):
                        print('Not enough money!\n')
                        continue
                    print(self.get_update(card, to, amount))
            elif choice == '4':
                self.get_update(From=card, close=True)
                return
            elif choice == '5':
                print('You have successfully logged out.\n')
                return
            elif choice == '0':
                print('Bye!')
                exit()
            else:
                print('Unknown option.\n')


System = BankingSystem()
System.menu()
