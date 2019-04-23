import inspect
import re
import shlex

class Rule:
    def __init__(self, route: str, handler):
        self.route = shlex.split(route)
        self.handler = handler

    def match(self, candidate):
        """"""
        tokens = shlex.split(candidate)
        if len(tokens) != len(self.route):
            return False

        keywords = dict()
        for rule, token in zip(self.route, tokens):
            match = re.fullmatch('<([^>]+)>', rule)
            # If it is a capture token, capture it as a named argument
            if match:
                keywords[match.group(1)] = token

            # If it is not a capture token, it must be a string literal.
            # If the string literal does not match the token from the rule,
            # this rule is not a match; return False.
            elif rule != token:
                return False

        # Ensure arguments match the handler's signature
        try:
            inspect.signature(self.handler).bind(**keywords)
        except TypeError:
            return False

        self.handler(**keywords)
        return True


class TestClass:
    def test_match_FindsGoodMatchNoArgs(self):
        rule = Rule('name', lambda: print('foo'))
        assert rule.match('name')

    def test_match_FindsGoodMatchOneParam(self):
        rule = Rule('<name>', lambda name: print(name))
        assert rule.match('foo')

    def test_match_LiteralsAndArgs(self):
        rule = Rule('new <name> <value>',
                    lambda name, value: print('Created tag {} {}'.format(
                        name, value)))
        assert rule.match('new db divebiologist')

    def test_match_MultiwordArgs(self):
        rule = Rule('new <name> <value>',
                    lambda name, value: print('Created tag {} {}'.format(
                        name, value)))
        assert rule.match('new db "leave a message after the lionfish"')

    def test_match_BadSignature(self):
        rule = Rule('<foo>', lambda bar: print(bar))
        assert not rule.match('hello, world')


class Dispatcher:
    def __init__(self):
        self.rules = set()

    def register(self, signature, handler):
        pass

    def dispatch(self, command):
        for rule in self.rules:
            if rule.match(command):
                break
