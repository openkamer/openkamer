import datetime


def years_from_str_list(year_start):
    start_date = datetime.date(year=int(year_start), month=1, day=1)
    current_date = start_date
    today = datetime.date.today()
    years = []
    while current_date.year <= today.year:
        years.append(str(current_date.year))
        current_date = datetime.date(year=current_date.year + 1, month=1, day=1)
    years.reverse()
    return years
