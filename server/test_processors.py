import unittest
from processors import *
from request_handler import RequestHandler
from hashlib import md5


class TestProcessor(unittest.TestCase):
    rh = RequestHandler()
    unpack = rh.unpack_resp

    pr = Processor()

    nick = 'test_user'
    ip = 'test_ip',
    pswd = '009b9edb38b800110ae4b25e1b0f9953'
    request_id = '0'
    session_id = 'e39216f13f168815497264e2e2b3c72d'

    def test__contains(self):
        db = sqlite3.connect(':memory:')
        db.create_function('CONTAINS', 2, self.pr._contains)
        c = db.cursor()
        c.execute('''CREATE TABLE test (c2 text)''')
        c.execute('''INSERT INTO test
                     VALUES ('str1,str2')''')
        c.execute('''INSERT INTO test
                     VALUES ('')''')

        c.execute('''SELECT * FROM test
                     WHERE CONTAINS(c1, 'r2')''')
        self.assertIsNone(c.fetchone())

        c.execute('''SELECT * FROM test
                     WHERE CONTAINS(c1, 'str1')''')
        self.assertIsNotNone(c.fetchone())

        db.commit()
        db.close()

    def test__add_session(self):
        _add_session = self.pr._add_session
        s_c = self.pr.s_c

        _add_session(self.nick, self.ip)
        s_c.execute('''SELECT * FROM sessions
                       WHERE name = ? AND session_id = ?
                       AND ip = ?''', (self.nick, self.session_id, self.ip))
        self.assertIsNotNone(s_c.fetchone())

        with self.assertRaises(BadRequest):
            _add_session(self.nick, self.ip)

        self.pr._close_session(self.session_id)
        self.pr.s_db.commit()

    def test__check_session(self):
        _check_session = self.pr._check_session

        act_nick = _check_session(session_id, ip)
        self.assertEqual(self.nick, act_nick)

        with self.assertRaises(BadRequest):
            _check_session(self.session_id + '0', self.ip)

        self.pr._close_session(session_id)

    def test__pack(self):
        act1 = self.pr._pack('0', 1, [(2, 3), 4])
        exp1 = b'"0",1,[[2,3],4]'
        self.assertEqual(act1, exp1)

    def test__comma_split(self):
        _comma_split = self.pr._comma_split

        act1 = _comma_split('str1,str2')
        exp1 = ['str1', 'str2']
        self.assertListEqual(act1, exp1)

        act2 = _comma_split('')
        exp2 = []
        self.assertListEqual(act2, exp2)

    def test__close_session(self):
        s_c = self.pr.s_c

        self.pr._close_session(self.session_id)
        s_c.execute('''SELECT * FROM sessions
                       WHERE session_id = ?''', (self.session_id,))
        self.assertIsNone(s_c.fetchone())
        self.pr.s_db.commit()

    def test__remove_from(self):
        _remove_from = self.pr._remove_from
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', 'item', '', 'item1,item2', '1,2,3')''', (self.nick,))

        _remove_from(self.nick, 'item', 'friends')
        _remove_from(self.nick, 'item', 'favorites')
        _remove_from(self.nick, 'item1', 'blacklist')
        _remove_from(self.nick, '2', 'dialogs')

        u_c.execute('''SELECT * FROM users
                       WHERE name = ?''', (self.nick,))
        row = tuple(u_c.fetchone())[2:]
        exp = ('', '', 'item2', '1,3')
        self.assertTupleEqual(row, exp)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        self.pr.u_db.commit()
        with self.assertRaises(BadRequest):
            _remove_from(self.nick, 'item', 'friends')

    def test__is_blacklisted(self):
        _is_blacklisted = self.pr._is_blacklisted
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', 'user1,user2', '')''', (self.nick,))

        self.assertTrue(_is_blacklisted(self.nick, 'user1'))

        self.assertFalse(_is_blacklisted(self.nick, 'user3'))

        self.assertFalse(_is_blacklisted(self.nick, self.nick))

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        self.assertFalse(_is_blacklisted(self.nick, 'user1'))

        self.pr.u_db.commit()

    def test__remove_add_request(self):
        r_c = self.pr.r_c
        _remove_add_request = self.pr._remove_add_request

        r_c.execute('''INSERT INTO requests
                       VALUES (?, 'user', 'test request')''')

        _remove_add_request(self.nick, 'user')
        _remove_add_request(self.nick, 'user')

        r_c.execute('''SELECT FROM requests
                       WHERE from_who = ? AND to_who = 'user' ''', (self.nick,))
        self.assertIsNone(r_c.fetchone())
        self.pr.r_db.commit()

    def test__add_to(self):
        _add_to = self.pr._add_to
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', 'item', '', 'item1,item2', '')''', (self.nick,))

        _add_to(self.nick, 'item3', 'friends')
        _add_to(self.nick, 'item4', 'blacklist')
        _add_to(self.nick, 'item2', 'blacklist')

        u_c.execute('''SELECT friends, blacklist FROM users
                       WHERE name = ?''', (self.nick,))

        row = u_c.fetchone()
        self.assertEqual(row['friends'], 'item,item3')
        self.assertEqual(row['blacklist'], 'item1,item2,item4')

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        with self.assertRaises(BadRequest):
            _add_to(self.nick, 'item3', 'friends')

        self.pr.u_db.commit()

    def test__user_in_dialog(self):
        _user_in_dialog = self.pr._user_in_dialog
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '1,2')''', (self.nick,))

        _user_in_dialog(self.nick, 2)

        with self.assertRaises(BadRequest):
            _user_in_dialog(self.nick, '1')

        with self.assertRaises(BadRequest):
            _user_in_dialog(self.nick, 3)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        with self.assertRaises(BadRequest):
            _user_in_dialog(self.nick, 3)

        self.pr.u_db.commit()

    def test__delete_dialog(self):
        _delete_dialog = self.pr._delete_dialog
        u_c = self.pr.u_c
        m_c = self.pr.m_c
        user1 = '@first_user'
        user2 = '@other_user'

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '0,1')''', (self.nick,))
        msgs = ('', '', '', '')
        times = (0, 0, 0, 0)
        usrs = [(self.nick, user1) * 2,
                (self.nick, '~' + user1) * 2,
                (user1, user2) * 2]
        for i in range(2):
            m_c.execute('''CREATE TABLE "d{}" (content text,
                                               timestamp int,
                                               sender text)'''.format(i))
            m_c.executemany('''INSERT INTO "d{}"
                               VALUES (?, ?, ?)''', (zip(msgs, times, usrs[i])))

        _delete_dialog(0, self.nick)
        m_c.execute('''SELECT sender FROM "d0"''')
        senders = [i['sender'] for i in m_c.fetchall()]
        self.assertIn('~' + self.nick, senders)
        self.assertIn(user1, senders)

        _delete_dialog(1, self.nick)
        m_c.execute('''SELECT name FROM sqlite_master
                       WHERE name = 'd1' ''')
        self.assertIsNone(m_c.fetchone())

        _delete_dialog(2, self.nick)
        m_c.execute('''SELECT sender FROM "d2"''')
        senders = [i['sender'] for i in m_c.fetchall()]
        self.assertIn(user2, senders)
        self.assertIn(user1, senders)

        u_c.execute('''SELECT dialogs FROM users
                       WHERE name = ?''' (self.nick,))
        self.assertEqual(u_c.fetchone()['dialogs'], '')

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        m_c.execute('''DROP TABLE "d0"''')
        m_c.execute('''DROP TABLE "d2"''')

        self.pr.u_db.commit()
        self.pr.m_db.commit()

    def test__user_exists(self):
        _user_exists = self.pr._user_exists
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (self.nick,))

        _user_exists(self.nick)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        with self.assertRaises(BadRequest):
            _user_exists(self.nick)

    def test__valid_nick(self):
        _valid_nick = self.pr._valid_nick

        self.assertTrue(_valid_nick(self.nick))

        self.assertFalse(_valid_nick('0' * 20))

        self.assertFalse(_valid_nick('~hacker'))

        self.assertTrue(_valid_nick('Test Nick'))
        self.assertFalse(_valid_nick(' ' * 5))

    def test__next_free_dialog(self):
        _nfd = self.pr._next_free_dialog
        m_c = self.pr.m_c

        m_c.execute('''CREATE TABLE d0 (c)''')
        m_c.execute('''CREATE TABLE d2 (c)''')

        free1 = _nfd()
        self.assertEqual(free1, 1)

        m_c.execute('''CREATE TABLE d1 (c)''')

        free2 = _nfd()
        self.assertEqual(free2, 3)

        for i in range(3):
            m_c.execute('''DROP TABLE d{}'''.format(i))

        self.pr.m_db.commit()

    def test_register(self):
        register = self.pr.register
        u_c = self.pr.u_c

        resp1 = self.unpack(register(self.request_id, self.ip, self.nick, self.pswd))
        exp1 = (sc.register_succ.value, [self.request_id, self.session_id])
        self.assertTupleEqual(resp1, exp1)

        u_c.execute('''SELECT * FROM users
                       WHERE name = ? AND pswd = ?''', (self.nick, self.pswd_hash))
        self.assertTupleEqual(tuple(u_c.fetchone()), (self.nick, self.pswd, '', '', '', ''))

        u_c.execute('''SELECT * FROM profiles
                       WHERE name = ?''', (self.nick,))
        self.assertTupleEqual(tuple(u_c.fetchone()), (self.nick, '', '', 0, '', b''))

        resp2 = self.unpack(register(self.request_id, self.ip, self.nick, self.pswd))
        exp2 = (sc.register_error.value, [self.request_id])
        self.assertTupleEqual(resp2, exp2)

        resp3 = self.unpack(register(self.request_id, self.ip, '~' + self.nick, self.pswd))
        self.assertTupleEqual(resp3, exp2)

        u_c.execute('''DELETE FROM profiles
                       WHERE name = ?''', (self.nick,))
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        self.pr._close_session(self.session_id)
        self.pr.u_db.commit()

    def test_login(self):
        login = self.pr.login
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, ?, '', '', '', '')''', (self.nick, self.pswd))

        resp1 = self.unpack(login(self.request_id, self.ip, self.nick, self.pswd))
        exp1 = (sc.login_succ.value, [self.request_id, self.session_id])
        self.assertEqual(resp1, exp1)

        resp2 = self.unpack(login(self.request_id, self.ip, self.nick, self.pswd))
        exp2 = (sc.login_error, [self.request_id])
        self.assertEqual(resp2, exp2)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        resp3 = self.unpack(login(self.request_id, self.ip, self.nick, self.pswd))
        self.assertEqual(resp3, exp2)

        self.pr.u_db.commit()

    def test_search_username(self):
        search_username = self.pr.search_username
        u_c = self.pr.u_c
        s_c = self.pr.s_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (self.nick,))
        self.pr._add_session(self.nick, ip)
        users = ('user1', 'user10', 'user2')
        for i in users:
            u_c.execute('''INSERT INTO users
                           VALUES (?, '', '', '', '', '')''', (i,))

        resp1 = self.unpack(search_username(self.request_id, self.ip, self.session_id, 'user1'))
        exp1 = (sc.search_username_result.value, [self.request_id, ['user1', 'user10']])
        self.assertEqual(resp1[0], exp1[0])
        self.assertEqual(resp1[1][0], exp1[1][0])
        self.assertListEqual(sorted(resp1[1][1]), exp1[1][1])

        resp2 = self.unpack(search_username(self.request_id, self.ip, self.session_id, 'user'))
        exp2 = (sc.search_username_result.value, [self.request_id, ['user1', 'user10', 'user2']])
        self.assertEqual(resp2[0], exp2[0])
        self.assertEqual(resp1[1][0], exp1[1][0])
        self.assertListEqual(sorted(resp2[1][0]), exp2[1][0])

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        self.pr._close_session(self.session_id)
        for i in users:
            u_c.execute('''DELETE FROM users
                           WHERE name = ?''', (i,))

        self.pr.u_db.commit()

    def test_friends_group(self):
        friends_group = self.pr.friends.group
        _add_session = self.pr._add_session
        _close_session = self.pr._close_session
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', 'user1,user10,user2', 'user2', 'user3', '')''', (self.nick,))
        self.pr._add_session(self.nick, ip)
        users = ('user1', 'user10', 'user2', 'users3')
        for i in users:
            u_c.execute('''INSERT INTO users
                           VALUES (?, '', '', '', '', '')''', (i,))
        sess1 = _add_session('user1', '')
        sess2 = _add_session('user2', '')

        resp = self.unpack(friends_group(self.request_id, self.ip, self.session_id))
        exp = (sc.friends_group_response.value, [self.request_id, [['user1', 'user2'], ['user10'], ['user2'], ['user3']]])
        self.assertEqual(resp[0], exp[0])
        self.assertEqual(resp1[1][0], exp1[1][0])
        for i in range(len(resp[1][0])):
            self.assertListEqual(sorted(resp[1][1][i]), exp[1][1][i])

        _close_session(self.session_id)
        _close_session(sess1)
        _close_session(sess2)
        for i in users:
            u_c.execute('''DELETE FROM users
                           WHERE name = ?''', (i,))
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        self.pr.u_db.commit()

    def test_message_history(self):
        message_history = self.pr.message_history
        m_c = self.pr.m_c
        u_c = self.pr.u_c

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '0')''', (self.nick,))
        m_c.execute('''CREATE TABLE "d0" (content text,
                                          timestamp int,
                                          sender text)''')

        msgs = []
        for i in range(5):
            m_c.execute('''INSERT INTO "d0"
                           VALUES (?, ?, ?)''', (str(i), 50 * i, self.nick))
            msgs.append((str(i), i * 50, self.nick))

        with self.assertRaises(BadRequest):
            message_history(self.request_id, self.ip, self.session_id, -1, 0)

        resp1 = self.unpack(message_history(self.request_id, self.ip, self.session_id, 2, 0))
        exp1 = (sc.message_history.value, [self.request_id, msgs[-2:]])
        self.assertTupleEqual(resp1, exp1)

        resp2 = self.unpack(message_history(self.request_id, self.ip, self.session_id, 0, 0))
        exp2 = (sc.message_history.value, [self.request_id, msgs])
        self.assertTupleEqual(resp2, exp2)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        m_c.execute('''DROP TABLE "d0"''')

        self.pr.u_db.commit()
        self.pr.m_db.commit()

    def test_send_message(self):
        send_message = self.pr.send_message
        u_c = self.pr.u_c
        m_c = self.pr.m_c
        other_user = '@other_user'

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (self.nick,))
        m_c.execute('''CREATE TABLE "d0" (content text,
                                          timestamp int,
                                          sender text)''')
        m_c.execute('''INSERT INTO "d0"
                       VALUES ('0', 0, ?)''', (self.nick,))
        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', ?, '')''', (other_user, self.nick))

        msg_args = ('test', int(time.time() * 100), self.nick)
        resp1 = self.unpack(send_message(self.request_id, self.ip, self.session_id, *msg_args))
        exp1 = (sc.message_received.value, [self.request_id])
        self.assertTupleEqual(resp1, exp1)
        m_c.execute('''SELECT * FROM "d0"
                       WHERE content = ? AND timestamp = ?
                       AND sender = ?''', msg_args)
        self.assertIsNotNone(m_c.fetchone())

        with self.assertRaises(BadRequest):
            send_message(self.request_id, self.ip, self.session_id, '0' * 1001, 0, self.nick)

        m_c.execute('''INSERT INTO "d0"
                       VALUES ('0', 0, ?)''', (other_user,))
        with self.assertRaises(BadRequest):
            send_message(self.request_id, self.ip, self.session_id, *msg_args)

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        m_c.execute('''DROP TABLE "d0"''')
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (other_user,))

        self.pr.u_db.commit()
        self.pr.m_db.commit()

    def test_change_profile_section(self):
        change_profile_section = self.pr.change_profile_section
        u_c = self.pr.u_c
        change = 'test'

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (self.nick,))
        u_c.execute('''INSERT INTO profiles
                       VALUES (?, '', '', 0, '', x'')''', (self.nick,))

        resp = self.unpack(change_profile_section(self.request_id, self.ip, self.session_id, 0, change))
        exp = (sc.change_profile_section_succ.value, [self.request_id])
        self.assertTupleEqual(resp, exp)

        u_c.execute('''SELECT * FROM users
                       WHERE name = ?''', (self.nick,))
        self.assertEqual(change, u_c.fetchone()['status'])

        with self.assertRaises(BadRequest):
            change_profile_section(self.request_id, self.ip, self.session_id, 2, 'not_int')

        with self.assertRaises(BadRequest):
            change_profile_section(self.request_id, self.ip, self.session_id, 4, b'PNG')

        u_c.execute('''DELETE FROM profiles
                       WHERE name = ?''', (self.nick,))
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))

        self.pr.u_db.commit()

    def test_add_to_blacklist(self):
        add_to_blacklist = self.pr.add_to_blacklist
        u_c = self.pr.u_c
        r_c = self.pr.r_c
        user1 = '@other_user'
        user2 = '@first_user'

        u_c.execute('''INSERT INTO users
                       VALUES (?1, '', ?2, ?2, '', '')''', (self.nick, user1))
        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (user1,))
        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (user2,))
        r_c.execute('''INSERT INTO requests
                       VALUES (?, ?, '')''', (self.nick, user2))

        resp = self.unpack(add_to_blacklist(self.request_id, self.ip, self.session_id, user1))
        exp = (sc.add_to_blacklist_succ.value, [self.request_id])
        self.assertTupleEqual(resp, exp)

        with self.assertRaises(BadRequest):
            add_to_blacklist(self.request_id, self.ip, self.session_id, self.nick)

        u_c.execute('''SELECT friends, favorites, blacklist FROM users
                       WHERE name = ?''', (self.nick,))
        row = u_c.fetchone()
        self.assertEqual(row['friends'], '')
        self.assertEqual(row['favorites'], '')
        self.assertEqual(row['blacklist'], user1)

        r_c.execute('''SELECT * FROM requests
                       WHERE from_who = ? AND to_who = ?''', (self.nick,))
        self.assertIsNone(r_c.fetchone())

        u_c.execute('''DELETE FROM users
                       WHERE name = ? OR name = ?
                       OR name = ?''', (self.nick, user1, user2))

        self.pr.u_db.commit()
        self.pr.r_db.commit()

    def test_delete_from_friends(self):
        u_c = self.pr.u_c
        user1 = '@other_user'

        u_c.execute('''INSERT INTO users
                       VALUES (?1, '', ?2, ?2, '', '')''', (self.nick, user1))
        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (user1,))

        resp = self.pr.delete_from_friends(self.request_id, self.ip, self.session_id, user1)
        exp = (sc.delete_from_friends_succ.value, [self.request_id])
        self.assertTupleEqual(resp,exp)

        u_c.execute('''SELECT friends, favorites FROM users
                       WHERE name = ?''', (self.nick,))
        row = u_c.fetchone()
        self.assertEqual(row['friends'], '')
        self.assertEqual(row['favorites'], '')

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (user1,))

        self.pr.u_db.commit()

    def test_send_request(self):
        send_request = self.pr.send_request
        u_c = self.pr.u_c
        r_c = self.pr.r_c
        user1 = '@other_user'

        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (self.nick,))
        u_c.execute('''INSERT INTO users
                       VALUES (?, '', '', '', '', '')''', (user1,))

        resp = self.unpack(send_request(self.request_id, self.ip, self.session_id, user1, ''))
        exp = (sc.send_request_succ.value[self.request_id])
        self.assertTupleEqual(resp, exp)

        r_c.execute('''SELECT * FROM requests
                       WHERE from_who = ? AND to_who = ?
                       AND message = '' ''', (self.nick, user1))
        self.assertIsNotNone(r_c.fetchone())

        with self.assertRaises(BadRequest):
            send_request(self.request_id, self.ip, self.session_id, user1, '')

        r_c.execute('''DELETE FROM requests
                       WHERE from_who = ? AND to_who = ?''', (self.nick, user1))

        self.pr._add_to(user1, self.nick, 'friends')
        with self.assertRaises(BadRequest):
            send_request(self.request_id, self.ip, self.session_id, user1, '')

        self.pr._remove_from(user1, self.nick, 'friends')
        self.pr._add_to(user1, self.nick, 'friends')
        with self.assertRaises(BadRequest):
            send_request(self.request_id, self.ip, self.session_id, user1, '')

        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (self.nick,))
        u_c.execute('''DELETE FROM users
                       WHERE name = ?''', (user1,))

        self.pr.u_db.commit()
        self.pr.r_db.commit()
