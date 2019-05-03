import inspect
import re
import shlex

import pytest

class Rule:
    def __init__(self, route: str, handler):
        self.route = shlex.split(route)
        self.handler = handler

    def __len__(self):
        return len(self.route)

    def __eq__(self, other):
        if len(self) != len(other):
            return False
        elif self.capture_positions() != other.capture_positions():
            return False
        pcps1 = list(sorted(self.processed_cps()))
        pcps2 = list(sorted(other.processed_cps()))
        if pcps1 != pcps2:
            return False
        for i in pcps1:
            x = re.fullmatch(r'<[^:]*:([^>]*)>', self.route[i])
            y = re.fullmatch(r'<[^:]*:([^>]*)>', other.route[i])
            if x.group(1) != y.group(1):
                return False
        return True
            

    def capture_positions(self):
        res = set()
        for i,x in enumerate(self.route):
            if re.fullmatch(r'<([^>]+)>', x):
                res.add(i)
        return res

    def processed_cps(self):
        res = set()
        for i,x in enumerate(self.route):
            if re.fullmatch(r'<[^:]*:[^>]*>', x):
                res.add(i)
        return res

    def fields(self):
        fields = 0
        for rule in self.route:
            if re.fullmatch(r'<([^>]+)>', rule):
                fields += 1
        return fields

    def processed_fields(self):
        fields = 0
        for rule in self.route:
            if re.fullmatch(r'<[^:]*:[^>]*>', rule):
                fields += 1
        return fields

    def match(self, candidate):
        """"""
        tokens = shlex.split(candidate)
        if len(tokens) != len(self.route):
            return False, None

        keywords = dict()
        for rule, token in zip(self.route, tokens):
            match = re.fullmatch(r'<([a-zA-Z0-9_]+(:[^>]+)?)>', rule)
            # If it is a capture token, capture it as a named argument
            if match:
                print(rule)
                if ':' in match.group(1):
                    parts = match.group(1).split(':')
                    print(':'.join(parts[1:]))
                    parser = eval(':'.join(parts[1:]))
                    try:
                        keywords[parts[0]] = parser(token)
                    except:
                        return False, None
                else:
                    keywords[match.group(1)] = token

            # If it is not a capture token, it must be a string literal.
            # If the string literal does not match the token from the rule,
            # this rule is not a match; return False.
            elif rule != token:
                return False, None

        # Ensure arguments match the handler's signature
        try:
            inspect.signature(self.handler).bind(**keywords)
        except TypeError:
            return False, None

        return True, self.handler(**keywords)


class TestClass:
    def test_match_FindsGoodMatchNoArgs(self):
        rule = Rule('name', lambda: print('foo'))
        assert rule.match('name')[0]

    def test_match_FindsGoodMatchOneParam(self):
        rule = Rule('<name>', lambda name: print(name))
        assert rule.match('foo')[0]

    def test_match_LiteralsAndArgs(self):
        rule = Rule('new <name> <value>',
                    lambda name, value: print('Created tag {} {}'.format(
                        name, value)))
        assert rule.match('new db divebiologist')[0]

    def test_match_MultiwordArgs(self):
        rule = Rule('new <name> <value>',
                    lambda name, value: print('Created tag {} {}'.format(
                        name, value)))
        assert rule.match('new db "leave a message after the lionfish"')[0]

    def test_match_BadSignature(self):
        rule = Rule('<foo>', lambda bar: print(bar))
        assert not rule.match('hello')[0]

    def test_match_ProcessorFunc(self):
        rule = Rule('<foo:int>', lambda foo: foo + 1)
        assert rule.match('9')[1] == 10

    def test_match_LambdaProcessorFunc(self):
        rule = Rule('"<foo:lambda x: int(x) + 1>"', lambda foo: foo)
        assert rule.match('9')[1] == 10

    def test_match_BadProcessor(self):
        rule = Rule('<foo:int>', lambda foo: foo + 1)
        assert not rule.match('bar')[0]


class Dispatcher:
    KEY = lambda x: (x.fields(), x.fields() - x.processed_fields())
    def __init__(self):
        self.rules = list()

    def register(self, signature, handler):
        candidate = Rule(signature, handler)
        for rule in self.rules:
            if rule == candidate:
                raise KeyError('That signature is already registered.')
        self.rules.append(candidate)
        self.rules.sort(key=Dispatcher.KEY)

    def dispatch(self, command):
        for rule in self.rules:
            success, res = rule.match(command)
            if success:
                return res


class TestDispatcher:
    def test_dispatch_UsesMostPreciseRule(self):
        d = Dispatcher()
        d.register('<foo>', lambda foo: 1)
        d.register('bar', lambda: 2)
        assert d.dispatch('bar') == 2

    def test_dispatch_UsesMostPreciseRule(self):
        d = Dispatcher()
        d.register('<foo>', lambda foo: 1)
        d.register('<foo:int>', lambda foo: 2)
        assert d.dispatch('9') == 2
        
    def test_register_RejectsIdenticalRules(self):
        d = Dispatcher()
        d.register('<foo>', lambda foo: 1)
        with pytest.raises(KeyError):
            d.register('<bar>', lambda bar: 2)
