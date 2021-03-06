from .. import udB


def get_stuff(key="WARNS"):
    kk = udB.get(key)
    if not kk:
        return {}
    try:
        return eval(kk)
    except BaseException:
        udB.delete(key)
    return {}


def add_warn(chat, user, count, reason):
    x = get_stuff()
    try:
        x[chat].update({user: [count, reason]})
    except BaseException:
        x.update({chat: {user: [count, reason]}})
    return udB.set("WARNS", str(x))


def warns(chat, user):
    x = get_stuff()
    try:
        count, reason = x[chat][user][0], x[chat][user][1]
        return count, reason
    except BaseException:
        return 0, None


def reset_warn(chat, user):
    x = get_stuff()
    try:
        x[chat].pop(user)
        return udB.set("WARNS", str(x))
    except BaseException:
        return
