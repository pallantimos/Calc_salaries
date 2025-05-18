REPORT_HANDLERS = {}


def registr_report(filenames):
    def decorator(func):
        REPORT_HANDLERS[name] = func
        return func
    return decorator


@registr_report
def calc_from_file():
    with open('payout', "r") as payout:

