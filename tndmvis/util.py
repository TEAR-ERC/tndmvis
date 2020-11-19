from sys import stdout
import os.path

class Progress:
    def __init__(self, total):
        self.total = total

    def __enter__(self):
        return self

    def __exit__(self, typ, value, tb):
        stdout.write('\n')
        stdout.flush()

    def update(self, step):
        bar_len = 60
        count = step + 1
        filled_len = int(round(bar_len * count / float(self.total)))

        percents = round(100.0 * count / float(self.total), 1)
        bar = '=' * filled_len + '-' * (bar_len - filled_len)

        stdout.write('[%s] %s%s\r' % (bar, percents, '%'))
        stdout.flush()

def is_valid_file(parser, arg):
    if not os.path.exists(arg):
        parser.error('The file {} does not exist.'.format(arg))
    else:
        return arg
