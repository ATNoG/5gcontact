import re


class LogParser:

    @staticmethod
    def parse(f_in, f_out):
        with open(f_in, 'r') as f_in:
            line_ = f_in.readline()
            lines_ = []
            while line_:
                line_ = f_in.readline()
                lines_.append(line_)
                if len(lines_) >= 20:
                    LogParser.parse_lines(lines_, f_out)
                    lines_ = []
            # print(lines_)
            LogParser.parse_lines(lines_, f_out)

    @staticmethod
    def parse_lines(lines, file):
        regex = '.*\\$\\$(.*)\\$\\$.*'
        m_lines = [re.match(regex, line).group(1).replace('|', ',') + '\n' for line in lines if re.match(regex, line)]

        if m_lines:
            with open(file, 'a') as f_out:
                # print(m_lines)
                f_out.writelines(m_lines)
