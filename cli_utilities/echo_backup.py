# pylint: disable=no-member,line-too-long

import argparse
import base64
import bz2
import getpass

from nacl.secret import SecretBox


parser = argparse.ArgumentParser(description='Decrypt and echo a Passive Data Kit backup file.')

parser.add_argument('file', type=str, nargs='+', help='paths of files to decrypt and echo')

parser.add_argument('--key', type=str, help='backup encryption key')

args = vars(parser.parse_args())

print(str(args))

if args['key'] is None:
    args['key'] = getpass.getpass('Enter the backup encryption key: ')

key = base64.b64decode(args['key'])

for file in args['file']:
    box = SecretBox(key)

    with open(file, 'rb') as backup_file:
        encrypted_content = backup_file.read()

        content = box.decrypt(encrypted_content)

        decompressed = bz2.decompress(content)

        print(decompressed)
