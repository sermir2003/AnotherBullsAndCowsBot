import telebot
from telebot import types
import random
import enum

TOKEN = '5854773198:AAHCxcsaHXpqN_hioYnpPMIDEI0GCMpszS8'

BOT_DESCRIPTION = 'С этим ботом вы можете сыграть в "Быки и коровы" — логическую игру, в ходе которой один из игроков должен определить последовательность, которую задумал второй игрок.'

RULES_OF_GAME = """
Вам предлагается сыграть в классический вариант игры "Быки и коровы" против бота.
Бот задумал тайное 4-значное число с неповторяющимися цифрами, ваша задача отгадать число, совершив как можно меньше попыток.
Во время каждой попытки вам предлагается отправить боту 4-значное число с неповторяющимися цифрами. Бот сообщает в ответ, сколько цифр угадано без совпадения с их позициями в тайном числе (то есть количество коров) и сколько угадано вплоть до позиции в тайном числе (то есть количество быков).
Например:
Задумано тайное число "3219".
Попытка: "2310".
Результат: две "коровы" (две цифры: "2" и "3" — угаданы на неверных позициях) и один "бык" (одна цифра "1" угадана вплоть до позиции).
"""
BOT_INVITATION = 'Чего бы вы хотели?'

INTERRUPT_SUGGESTION = 'Последняя игра не закончена, заверить её?'

ERROR_GUESSING = """
Неопознанная команда, ожидалость число или команды `Прервать` или `Отмена`
Чсило должно быть четырёхзначным, состоять из цифр от 0 до 9 включительно, не должно начинаться с 0 и не должно иметь повторяющихся цифр.
"""

bot = telebot.TeleBot(TOKEN)

class State(enum.Enum):
    NOT_STARTED = 0
    GAME_RUN = 1
    INTERRUPTING = 2

class GameState:
    def __init__(self, password) -> None:
        self.password = password
        self.number_moves = 0

machine_state = {}  # user interaction state
game_state = {}  # user interaction state

def get_state(user_id):
    return machine_state.get(user_id, State.NOT_STARTED)

def classic_password_gen():
    alphabet = list(range(1, 10))
    random.shuffle(alphabet)
    zero_pos = random.randint(1, 10)
    alphabet = alphabet[:zero_pos] + [0] + alphabet[zero_pos:]
    return ''.join(map(str, alphabet[:4]))

def might_be_guess(message):
    line = message.text.strip()
    digits = set(line)
    alphabet = set(map(str, range(0, 10)))
    return (len(line) == 4) and (len(digits) == 4) and (digits <= alphabet) and (line[0] != '0')

def interrupt_game(message):
    bot.send_message(message.chat.id, 'Игра завершена, было загадано число {}'.format(game_state[message.chat.id].password))
    machine_state[message.chat.id] = State.NOT_STARTED
    game_state.pop(message.chat.id)
    invitation(message)

def finish_game_victory(message):
    bot.send_message(message.chat.id, 'Поздравляю, вы угадали!\nИспользовано попыток: {}'.format(str(game_state[message.chat.id].number_moves)))
    machine_state[message.chat.id] = State.NOT_STARTED
    game_state.pop(message.chat.id)
    invitation(message)

@bot.message_handler(commands=['start'], func=lambda message: get_state(message.chat.id) == State.NOT_STARTED)
def start(message):
    bot.send_message(message.chat.id, BOT_DESCRIPTION)
    invitation(message)

def invitation(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_1 = types.KeyboardButton('Правила')
    item_2 = types.KeyboardButton('Начать игру')
    markup.add(item_1, item_2)
    bot.send_message(message.chat.id, BOT_INVITATION, reply_markup=markup)

@bot.message_handler(commands=['start'], func=lambda message: get_state(message.chat.id) == State.GAME_RUN)
def suggest_interruption(message):
    machine_state[message.chat.id] = State.INTERRUPTING
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item_1 = types.KeyboardButton('Прервать')
    item_2 = types.KeyboardButton('Отмена')
    markup.add(item_1, item_2)
    bot.send_message(message.chat.id, INTERRUPT_SUGGESTION, reply_markup=markup)

@bot.message_handler(func=lambda message: get_state(message.chat.id) == State.INTERRUPTING)
def interruption_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Прервать')
    markup.add(item)
    if message.text == 'Прервать':
        interrupt_game(message)
    elif message.text == 'Отмена':
        machine_state[message.chat.id] = State.GAME_RUN
        bot.send_message(message.chat.id, 'Игра продолжается, вводите ваши предположения', reply_markup=markup)
    elif might_be_guess(message):
        machine_state[message.chat.id] = State.GAME_RUN
        bot.send_message(message.chat.id, 'Игра продолжается', reply_markup=markup)
        guess_handler(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item_1 = types.KeyboardButton('Прервать')
        item_2 = types.KeyboardButton('Отмена')
        markup.add(item_1, item_2)
        bot.reply_to(message, ERROR_GUESSING, reply_markup=markup)

@bot.message_handler(content_types='text', func=lambda message: get_state(message.chat.id) == State.GAME_RUN)
def guess_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item = types.KeyboardButton('Прервать')
    markup.add(item)
    if might_be_guess(message):
        game_state[message.chat.id].number_moves += 1
        actual_number = game_state[message.chat.id].password
        user_attempt = message.text.strip()
        number_bulls = 0
        number_cows = 0
        for i in range(4):
            if user_attempt[i] == actual_number[i]:
                number_bulls += 1
            elif user_attempt[i] in actual_number:
                number_cows += 1
        bot.send_message(message.chat.id, 'Быков: ' + str(number_bulls) + '; коров: ' + str(number_cows), reply_markup=markup)
        if number_bulls == 4:
            finish_game_victory(message)
    elif message.text == 'Прервать':
        interruption_handler(message)
    else:
        bot.reply_to(message, ERROR_GUESSING, reply_markup=markup)

@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, 'The developer also needs help.')

@bot.message_handler(content_types='text', func=lambda message: get_state(message.chat.id) == State.NOT_STARTED)
def basic_functionality(message):
    if message.text == 'Правила':
        bot.send_message(message.chat.id, RULES_OF_GAME)
        invitation(message)
    elif message.text == 'Начать игру':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item = types.KeyboardButton('Прервать')
        markup.add(item)
        password = classic_password_gen()
        machine_state[message.chat.id] = State.GAME_RUN
        game_state[message.chat.id] = GameState(password)
        bot.send_message(message.chat.id, 'Число сгенерировано! Вводите ваши предположения. Для того, чтобы завершить игру отправьте `Прервать`', reply_markup=markup)
    else:
        bot.reply_to(message, 'Неопознанная команда, ожидался запрос `Правила` или `Начать игру`')

@bot.message_handler()
def default_handler(message):
    bot.reply_to(message, 'Неопознанная команда')

bot.polling(none_stop=True, interval=0)
