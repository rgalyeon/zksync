# RANDOM WALLETS MODE
RANDOM_WALLET = True  # True or False

# removing a wallet from the list after the job is done
REMOVE_WALLET = False

SLEEP_FROM = 500  # Second
SLEEP_TO = 800  # Second

QUANTITY_THREADS = 1

THREAD_SLEEP_FROM = 300
THREAD_SLEEP_TO = 600

# PROXY MODE
USE_PROXY = False

# GWEI CONTROL MODE
CHECK_GWEI = True  # True or False
MAX_GWEI = 25
REALTIME_GWEI = True  # если включен, то будет считывать гвей из файла realtime_settings.json в реалтайме

# Рандомизация гвея. Если включен режим, то максимальный гвей будет выбираться из диапазона
RANDOMIZE_GWEI = True  # if True, max Gwei will be randomized for each wallet for each transaction
MAX_GWEI_RANGE = [24, 27]

GAS_SLEEP_FROM = 100
GAS_SLEEP_TO = 600

GAS_MULTIPLIER = 1

# RETRY MODE
RETRY_COUNT = 3

# INCH API KEY
INCH_API_KEY = ""
