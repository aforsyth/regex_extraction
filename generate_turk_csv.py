import argparse


def main(input_filename):
    pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_filename', required=True,
                        help=('Path to an RPDR formatted '
                              'text file, e.g. /Users/user1/../file.txt'))
    args = parser.parse_args()
    main(args.input_filename)
