# fight_simulator/utils/logger.py
class Logger:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    @staticmethod
    def title(msg):
        print(Logger.HEADER + msg + Logger.ENDC)

    @staticmethod
    def action(msg):
        print(Logger.OKBLUE + msg + Logger.ENDC)

    @staticmethod
    def damage(msg):
        print(Logger.FAIL + msg + Logger.ENDC)

    @staticmethod
    def buff(msg):
        print(Logger.OKGREEN + msg + Logger.ENDC)

    @staticmethod
    def info(msg):
        print(Logger.WARNING + msg + Logger.ENDC)

    @staticmethod
    def warning(msg):
        print(Logger.WARNING + msg + Logger.ENDC)