import sys
import re
import csv


def parse(lines, file):
    regex = '.*\\$\\$(.*)\\$\\$.*'
    m_lines = [re.match(regex, line).group(1).replace('|', ',') + '\n' for line in lines if re.match(regex, line)]

    if m_lines:
        with open(file, 'a') as f_out:
            # print(m_lines)
            f_out.writelines(m_lines)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python ts_collector.py <run_name> <in_file>')
        exit(2)

    with open(sys.argv[2], 'r') as f_in:
        line_ = f_in.readline()
        lines_ = []
        while line_:
            line_ = f_in.readline()
            lines_.append(line_)
            if len(lines_) >= 20:
                parse(lines_, sys.argv[1])
                lines_ = []
        # print(lines_)
        parse(lines_, sys.argv[1])
