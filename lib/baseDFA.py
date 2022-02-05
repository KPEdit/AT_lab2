import typing
from itertools import combinations
from base import *
from SyntaxTree import SyntaxTree, Node
from enum import Enum
import queue

class DFANode:
  pass

class State(Enum):
  SUPER = 3
  END = 2
  START = 1
  BASE = 0

class DFATransition:
  _from: DFANode
  value: str
  _to: DFANode

  def __init__(self, _from: DFANode, _to: DFANode, value: str):
    self._from = _from
    self.value = value
    self._to = _to

  def __str__(self) -> str:
    return f"{self._from} -> {self._to} | {self.value}"

  @property
  def go(self):
    return self._to

class DFANode:
  nodes: typing.List[DFATransition]
  treeNodes: typing.Set[int]
  _isStart: bool
  _isEnd: bool
  groups: typing.List[int]

  def __init__(self, isStart=False, isEnd=False, treeNodes={}):
    self.nodes = list()
    self.treeNodes = treeNodes
    self.groups = set()
    self._isStart = isStart
    self._isEnd = isEnd

  @property
  def state(self):
    if self._isEnd and self._isStart:
      return State.SUPER
    elif self._isEnd:
      return State.END
    elif self._isStart:
      return State.START
    return State.BASE

  @state.setter
  def state(self, var: State):
    if var == State.SUPER:
      self._isEnd = True
      self._isStart = True
    elif var == State.END:
      self._isEnd = True
      self._isStart = False
    elif var == State.START:
      self._isEnd = False
      self._isStart = True
    else:
      self._isEnd = False
      self._isStart = False

  def addGroups(self, ids):
    for n in self.treeNodes:
      self.groups = self.groups | set(ids[n].groups)

  def concatGroups(self, nodes):
    for n in nodes:
      self.groups |= n.groups

  def __str__(self) -> str:
    return f"id={id(self)}; nodes={len(self.nodes)}; state={self.state} g={self.groups}"

  def __repr__(self) -> str:
    return f"id={id(self)}; nodes={len(self.nodes)}; state={self.state} g={self.groups}"

  def add(self, _to: DFANode, value: str):
    tos = [True for t in self.nodes if (t.value == value and t._to == _to)]
    if not tos:
      trs = DFATransition(self, _to, value)
      self.nodes.append(trs)

  def go(self, s: str):
    vals = [t.value for t in self.nodes]
    if s in vals:
      i = vals.index(s)
      return self.nodes[i].go
    return None
  
  def getChars(self):
    chars = set()
    for n in self.nodes:
      chars.add(n.value)
    return chars

  def getNodeByChar(self, char):
    for n in self.nodes:
      if n.value == char:
        return n


class DFA:
  head: DFANode
  visited: typing.Set[DFANode]
  unvisited_set: typing.Set[DFANode]
  # groups: typing.Dict[int, str]
  __Rijk_dict: typing.Dict[str, list]

  def __init__(self):
    self.clear()

  def clear(self):
    self.visited = set()
    self.unvisited_set = set()
    # self.groups = dict()
    self.__Rijk_dict = dict()
    self.head = None
    
  def build(self, tree: SyntaxTree):
    follows, ids = tree.genFollowposes()
    root_fp = tree.root.firstpos()
    head = DFANode(isStart=True, treeNodes=root_fp)
    head.addGroups(ids)
    self.unvisited_set.add(head)
    while not not self.unvisited_set:
      tmp = self.unvisited_set.pop()
      self.visited.add(tmp)
      char_set = self.__genCharSet(tmp, ids)
      for c in char_set:
        U = self._fpUnion(tmp, follows, c, ids)
        boolV, node = self._visited_check(U)
        if not boolV:
          node = DFANode(treeNodes=U)
          node.addGroups(ids)
          if c == r'\$':
            if tmp.state == State.START:
              tmp.state = State.SUPER
            else:
              tmp.state = State.END
          else:
            self.unvisited_set.add(node)
        if c != r'\$':
          tc = c
          if len(c) > 1 and c[0] == '\\':
            tc = c[1]
          tmp.add(node, tc)
    self.head = head
    return head

  """SIMPLE DFA"""
  def bfs(self, debug=False):
    v = set()
    go = [self.head]
    while go:
      if debug:
        print(go)
      tmp = go.pop(0)
      yield tmp
      if not id(tmp) in v:
        v.add(id(tmp))
        gotmp = []
        for t in tmp.nodes:
          if id(t._to) not in v and t._to not in gotmp:
            gotmp.append(t._to)
        go = gotmp + go

  def _visited_check(self, U: typing.Set[int]):
    for k in self.visited:
      if k.treeNodes == U:
        return (True, k)
    return (False, None)

  def __genCharSet(self, node: DFANode, ids: typing.Dict[int, Node]):
    cs = set()
    for k in node.treeNodes:
      cs.add(ids[k].value.value)
    return cs

  def _fpUnion(self, cur: DFANode, follows: typing.Dict[int, typing.Set[int]], 
    cchar: str, ids: typing.Dict[int, Node]) -> typing.Set[int]:
    U = set()
    for c in cur.treeNodes:
      if ids[c].value.value == cchar:
        if c in follows:
          U |= follows[c]
    return U

  """MINIMIZE DFA"""
  def minimize(self):
    S = set([i for i in self.bfs()])
    F = set([i for i in S if i._isEnd])
    S_F = S - F
    G = [F, S_F]
    # print("BEFORE SPLIT")
    # print(G, len(G))
    P = self._minEQ(G)
    # print("AFTER SPLIT")
    # print(P, len(P))
    min_dfa = DFA()
    new_nodes = [DFANode() for i in range(len(P))]
    for i, node in enumerate(new_nodes):
      for l in P[i]:
        if l._isEnd:
          node._isEnd = True
        if l._isStart:
          node._isStart = True
          min_dfa.head = node
        for j in l.nodes:
          k = self.__minGetIndex(j._to, P)
          if k != i or (k == i and j._to == j._from):
            node.add(new_nodes[k], j.value)
    return min_dfa

  def __minGetIndex(self, node, groups):
    for i,n in enumerate(groups):
      if node in n:
        return i
    raise RuntimeError("Illegal DFA")

  def _minEQ(self, G):
    chars = self._getChars()
    tasks = queue.SimpleQueue()
    for c in chars:
      tasks.put((G[0], c))
      tasks.put((G[1], c))
    nG = [i for i in G]
    while not tasks.empty():
      C, a = tasks.get()
      for R in G:
        r1, r2 = self._minSplit(R, C, a)
        if r1 and r2:
          nG.remove(R)
          nG.append(r1)
          nG.append(r2)
          for c in chars:
            tasks.put((r1, c))
            tasks.put((r2, c))
      G = nG
    return G
          
  def _minSplit(self, R, C, a):
    r1 = set()
    for n in R:
      for t in n.nodes:
        if t.value == a and t._to in C:
          r1.add(n)
    r2 = R - r1
    return r1, r2

  def _getChars(self):
    chars = set()
    for node in self.bfs():
      chars |= node.getChars()
    return chars

  """GRAPH"""
  def _genName(self, i):
    i = max(0, i)
    if i == 0:
      return 'A'
    s = ''
    S = "ABCDEFGIJKLMNOPQESTUVWXYZ"
    while i > 0:
      c = i % len(S)
      s += S[c]
      i = i // len(S)
    return s[::-1]

  def genDot(self, outFile='DFAgraph'):
    s = "digraph G {"
    obhod = [t for t in self.bfs()]
    for i,n in enumerate(obhod):
      color = 'black'
      if n.state == State.START:
        color = 'green'
      elif n.state == State.END:
        color = 'red'
      elif n.state == State.SUPER:
        color = 'blue'
      s += f"{id(n)} [label=\"{self._genName(i)}\"; color={color}]"
      # s += f"{id(n)} [label=\"{id(n)%1000}\"; color={color}]"
    s += '; '
    for n in obhod:
      for t in n.nodes:
        s += f"{id(t._from)} -> {id(t._to)} [label=\"{t.value}\"]" 
        # s += f"{id(t._from)%1000} -> {id(t._to)%1000} [label=\"{t.value}\"]" 
    s += "}"
    with open(f'./{outFile}.dot', 'w') as out:
      out.write(s)
    import subprocess
    subprocess.call(['dot', '-Tpng', f'./{outFile}.dot', '-o', f'{outFile}.png'])

  """RIJK"""

  def __nameRIJK(self, i,j,k):
    return f"{i}_{j}_{k}"

  def _Rijk(self, nodes, i, j, k):
    key = self.__nameRIJK(i,j,k)
    if key in self.__Rijk_dict:
      return self.__Rijk_dict[key]
    if k == 0:
      if i == j:
        self.__Rijk_dict[key] = r"\#"
        return self.__Rijk_dict[key]
      node = nodes[i]
      dugs = ""
      for n in node.nodes:
        if n._to == nodes[j]:
          tt = n.value
          if n.value in SPECIALS:
            tt = "\\" + tt
          if dugs == "":
            dugs = tt
          else:
            dugs = f"{dugs}|{tt}"
      if len(dugs) > 1:
        dugs = f"({dugs})"
      self.__Rijk_dict[key] = dugs
      return self.__Rijk_dict[key]
    else:
      Rijk_1 = self._Rijk(nodes, i,j,k-1)
      Rikk_1 = self._Rijk(nodes, i,k,k-1)
      Rkkk_1 = self._Rijk(nodes, k,k,k-1)
      Rkjk_1 = self._Rijk(nodes, k,j,k-1)
      # tmp = f"{Rikk_1}"
      # if Rkkk_1 and Rkkk_1 != r"\#":
      #   tmp = f"{tmp}({Rkkk_1})*"
      # if Rkjk_1:
      #   tmp = f"{tmp}{Rkjk_1}"
      # if tmp:
      #   if Rijk_1:
      #     tmp = f"{Rijk_1}|{tmp}"
      # elif Rijk_1:
      #   tmp = f"{Rijk_1}"
      # if tmp:
      #   tmp = f"({tmp})"

      tmp = f"({Rijk_1}|{Rikk_1}({Rkkk_1})*{Rkjk_1})"
      self.__Rijk_dict[key] = tmp
      return tmp

  """USER FUNCTIONS"""
  def match(self, s):
    tmp = self.head
    try:
      for c in s:
        tmp = tmp.go(c)
      if tmp._isEnd:
        return True
    except:
      return False
    return False

  def kpath(self):
    nodes = [i for i in self.bfs()]
    i = 1
    j = []
    n = len(nodes)
    nodes = [0] + nodes
    for l in range(1,n+1):
      if nodes[l]._isEnd:
        j.append(l)
    A = []
    for l in j:
      A.append(self._Rijk(nodes, i,l,n))
    return A

  def dif(self, sec):
    fNodes = [i for i in self.bfs()]
    sNodes = [j for j in sec.bfs()]
    nodes = [[DFANode()]*len(sNodes) for i in range(len(fNodes))]
    head = nodes[0][0]
    head.state = State.START
    for i,fn in enumerate(fNodes):
      for trans in fn.nodes:
        for j,sn in enumerate(sNodes):
          if trans.value in sn.getChars():
            q1 = fNodes.index(trans._to)
            r1 = sNodes.index(sn.getNodeByChar(trans.value)._to)
            cur = nodes[i][j]
            cur.add(nodes[q1][r1], trans.value)
          if (fn._isEnd) and (not sn._isEnd):
            nodes[i][j]._isEnd = True
    dfa = DFA()
    dfa.head = head
    return dfa

if __name__ == '__main__':
  
  test = r"(a|b)*abb\$"
  test = r"(a(b|c))*c\$"
  test = r"(ab*a|b)*\$"
  test = r"(ab)|(ac)(a*)\$"
  test = r"(aba(a|b|c))*\$"
  test = r"a(a|b|c|([123456]*))\$"  #Good
  test = r"(aba[abc])*\$"
  # test = r"(aba[abc]){3}\$" #Good
  # test = r"(nan)*an\$"
  # test = r"asd*(nad)|((cur\{))as[123]{6}[]\#\$"
  # test = r"(ab*a|b)*\$"
  # test = r"(ab)|(ac)(a*)\$"
  test = r"(abc*|deb[123](ans|end))\$"

  tree = SyntaxTree()
  dfa = DFA()
  tree.build(test)
  head = dfa.build(tree)
  
  tree.root_null.genDot()
  dfa.genDot()
  min_dfa = dfa.minimize()
  min_dfa.genDot("minDFA")

  print("KPATH:")
  print(len(min_dfa.kpath()[1]))