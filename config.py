TOKEN = 'TOKEN'
currentpages = {}
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


def GetMainKeyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    button1 = InlineKeyboardButton("🔍 Найти ответ", callback_data='search')
    button2 = InlineKeyboardButton("🆘 Помощь", callback_data='help')

    markup.add(button1, button2)
    return markup

def GetGoBackKeyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    button1 = InlineKeyboardButton("🏠 В меню", callback_data='menu')
    markup.add(button1)
    return markup

def GetAnswerInlineKeyboard():
    markup = InlineKeyboardMarkup()
    button1 = InlineKeyboardButton("➡️ Следующий ответ", callback_data='next_answer')
    button2 = InlineKeyboardButton("◀️ К вопросам", callback_data='back')
    button3 = InlineKeyboardButton("🏠 В меню", callback_data='menu')
    markup.add(button2, button1)
    markup.add(button3)
    return markup
def GetQuestionKeyboard():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("👁 Посмотреть ответ", callback_data='show_answer'))
    markup.add(InlineKeyboardButton("⬅️ Предыдущий вопрос", callback_data='prev_question'),
                 InlineKeyboardButton("➡️ Следующий вопрос", callback_data='next_question'))
    markup.add(InlineKeyboardButton("🏠 В меню", callback_data='menu'))
    return markup
