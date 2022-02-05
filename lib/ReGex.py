from argparse import ArgumentError
import typing
from base import *
from SyntaxTree import SyntaxTree, Node
from baseDFA import *
from queue import SimpleQueue


class ReGex:
  tree: SyntaxTree
  dfa: DFA
  min_dfa: DFA
  pattern: str

  def __init__(self, pattern: str=""):
    self.pattern = pattern + r'\$'
    self.tree = SyntaxTree()
    self.dfa = DFA()
    self.tree.build(self.pattern)
    self.dfa.build(self.tree)
    self.min_dfa = self.dfa.minimize()

  def match(self, s: str):
    return self.min_dfa.match(s)

  def kPath(self):
    return self.min_dfa.kpath()
  
  def dif(self, sec):
    r = self.min_dfa.dif(sec.min_dfa)
    reg = ReGex()
    reg.min_dfa = r
    reg.pattern = reg.kPath()
    return reg

  def inv(self):
    if not self.tree:
      return ""
    t = self._inv(self.tree.root)
    return "".join(t.split(r'\$'))
  
  def _inv(self, node: Node):
    if node.nodes:
      if node.value.tag == CONCAT:
        n1 = self._inv(node.nodes[0])
        n2 = self._inv(node.nodes[1])
        return f"{n2}{n1}"
      elif node.value.tag == OR:
        n1 = self._inv(node.nodes[0])
        n2 = self._inv(node.nodes[1])
        return f"{n1}|{n2}"
      elif node.value.tag == KLINI:
        n = self._inv(node.nodes[0])
        return f"({n})*"
      elif node.value.tag == REPEATS:
        n = self._inv(node.nodes[0])
        return f"({n})" + "{%s}" % (node.value.value)
      else:
        return self._inv(node.nodes[0])
    return node.value.value


if __name__ == '__main__':
  test1 = "01{3}|10*"
  test2 = "aba"
  r1 = ReGex(test1)
  r2 = ReGex(test2)
  print(r1.inv())
  r1.min_dfa.genDot('test1')
  r1.dfa.genDot('test1dfa')
  a = r1.dfa.minimize()
  r1 = ReGex()
  r1.min_dfa = a
  r2.min_dfa.genDot('test2')
  r3 = r1.dif(r2)
  r3.min_dfa.genDot('r3')
  print()

  # test = r"(abc*|deb[123]|kick|pick)\$"
  # r1 = ReGex(test)
  # print(r1.match("abccccc"))
  # print(r1.match("deb1"))
  # print(r1.match("deb2"))
  # print(r1.match("deb3"))
  # print(r1.match("debk"))
  