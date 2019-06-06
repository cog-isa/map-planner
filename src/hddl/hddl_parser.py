import re
import mapcore.hddl.branch_parser as bch

class HTNParser:
    def __init__(self, domain_file, problem_file):
        with open(domain_file, 'r+') as dom:
            domain = dom.read()
        with open(problem_file, 'r+') as pr:
            problem = pr.read()
        self.domain = domain
        self.problem = problem
        self.utokens = []

    def get_tokens(self, text):
        return re.findall(':[a-z]*', text)

    def tokenizer(self, tokens):
        for val in tokens:
            yield val

    def ParseBlock(self, descr):
        block = {}
        tokens = self.get_tokens(descr)
        flag = False
        my_token = self.tokenizer(tokens)
        start_token = next(my_token)
        while not flag:
            try:
                if start_token not in self.utokens:
                    start_token = next(my_token)
                    continue
                next_token = next(my_token)
                while next_token not in self.utokens:
                    next_token = next(my_token)
                    continue
                part = [''.join(el) for el in descr.split(start_token)[1].split(next_token)][0]
                while part[-1] != ')':
                    part = part[:-1]
                else:
                    part = part[:-1]
                parsed = getattr(bch, 'parse_'+start_token[1:])(part)
                if isinstance(parsed, list):
                    block[start_token[1:]] = parsed
                else:
                    block.setdefault(start_token[1:]+'s', []).append(parsed)

                if next_token != start_token:
                    self.utokens.remove(start_token)
                start_token = next_token
                descr = descr.split(part)[1]

            except StopIteration:
                part = [''.join(el) for el in descr.split(start_token)][1]
                while part[-1] != ')':
                    part = part[:-1]
                else:
                    part = part[:-1]
                parsed = getattr(bch, 'parse_'+start_token[1:])(part)
                block.setdefault(start_token[1:] +'s', []).append(parsed)
                self.utokens.remove(start_token)
                flag = True
        return block

    def ParseDomain(self, descr):
        self.utokens = [':types', ':predicates', ':task', ':method', ':action']
        return self.ParseBlock(descr)

    def ParseProblem(self, descr):
        self.utokens = [':objects', ':htn', ':init']
        return self.ParseBlock(descr)

# if __name__ == '__main__':
#
#     domain_file = '../benchmarks/hierarchical/domain.hddl'
#     problem_file = '../benchmarks/hierarchical/task1.hddl'
#
#     parser = Parser(domain_file, problem_file)
#     domain = parser.ParseDomain(parser.domain)
#     problem = parser.ParseProblem(parser.problem)
#
#
#     ground(domain, problem)
#
#     htn = HTNSearch(signs)
#     plan = htn.search_plan()
#     print()

