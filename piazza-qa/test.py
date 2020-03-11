from piazza_api import Piazza
p = Piazza()
p.user_login('', '')

profile = p.get_user_profile()
print(profile)

course = p.network('k7gqop42az52ck')

print(course.get_feed())