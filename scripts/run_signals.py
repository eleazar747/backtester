import os
import sys

# ensure project root is on sys.path so project packages import correctly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stockmarket.settings')
import django

def main():
    try:
        django.setup()
    except Exception as e:
        print('Django setup error:', e)
        sys.exit(1)

    try:
        from strategy.processor.signals import generate_signals_for_all

        print('Running signal generator...')
        res = generate_signals_for_all(out_csv='results/signals.csv')
        if res:
            print('Signal generation completed, results/signals.csv written.')
        else:
            print('No results generated (no symbols or insufficient data).')
    except Exception as e:
        print('Error while generating signals:', e)
        raise


if __name__ == '__main__':
    main()
