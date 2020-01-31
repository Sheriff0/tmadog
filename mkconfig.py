import sys
import configparser

rc = configparser.ConfigParser (interpolation =
        configparser.ExtendedInterpolation ())

rc[configparser.DEFAULTSECT]['volatile'] = 'False'

rc[configparser.DEFAULTSECT]['indices'] = '0,0,0,0,0,0'

rc.read_dict ({
        'home': {},
        'login_form': {
            'keys': '[Matric Number]/[Password]',

            'path': 'Login',

            },

        'tma_page': {
            'path': '${login_form:path},${login_form:keys},Take TMA',
            },

        'profile_page': {

            'path': '${login_form:path},${login_form:keys}'
            }
        })

if __name__ == '__main__':
    with open (sys.argv[1], 'x') as f:
        rc.write (f)

