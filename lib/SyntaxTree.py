import typing
from base import *
from Lexer import Lexer, Token


class Node:
  pass

FollowPos = typing.NewType('FollowPos', typing.Dict[Node, typing.Set[Node]])

class Node:
  root: Node
  nodes: typing.List[Node]
  value: Token
  groups: typing.List[int]
  firstposes: typing.Set[Node]
  lastposes: typing.Set[Node]
  nullables: bool or None
  

  def __init__(
      self, 
      root: Node=None,
      value: Token=None):
    self.root = root
    self.value = value
    self.nodes = []
    self.groups = []
    self.firstposes = -1
    self.lastposes = -1
    self.nullables = -1
    
  
  def add(self, value: Token) -> Node:
    node = Node(self, value)
    self.nodes.append(node)
    return node

  def pop(self):
    return self.nodes.pop()

  def add_node(self, node: Node):
    node.root = self
    self.nodes.append(node)

  @property
  def last(self):
    return self.nodes[-1]

  @property
  def lvl(self):
    if self.root is None:
      return 0
    return self.root.lvl + 1

  @property
  def isNotEmpty(self):
    return not not self.nodes

  def leftRoot(self):
    if not self.nodes:
      yield self
    for n in self.nodes:
      n.leftRoot()

  def optLeftRoot(self):
    go = [t for t in self.nodes]
    while go:
      tmp = go.pop(0)
      yield tmp
      go = tmp.nodes + go

  def printTree(self):
    for t in self.optLeftRoot():
      print(t)

  def copy(self):
    return Node(self.root, self.value)

  def __str__(self) -> str:
    return f"(lvl={self.lvl}  id={id(self)}  p={id(self.root) if self.root else self.root}  v={self.value}) g={self.groups}"
    
  def __repr__(self) -> str:
    return f"(lvl={self.lvl}  id={id(self)}  p={id(self.root) if self.root else self.root}  v={self.value}) g={self.groups}"
    
  def genDot(self, outFile='graph'):
    s = "digraph G {"
    ids = set()
    obhod = [t for t in self.optLeftRoot()]
    for t in obhod:
      if t.root.value is not None:
        if id(t.root) not in ids:
          val = t.value.value
          if len(val) == 2:
            val = r'\\' + val
          s += f"{id(t.root)} [label=\"{val}\"]; "
          # s += f"{id(t.root)} [label=\"{id(t.root)}\"]; "
          
          ids.add(id(t.root))
      if id(t) not in ids:
        val = t.value.value
        if len(val) == 2:
          val = r'\\' + val
        s += f"{id(t)} [label=\"{val}\"]; "
        # s += f"{id(t)} [label=\"{id(t)}\"]; "
        ids.add(id(t))
    for t in obhod:
      if t.root.value is not None:
        s += f"{id(t.root)} -> {id(t)}; "
    s += "}"
    with open(f'./{outFile}.dot', 'w') as out:
      out.write(s)
    import subprocess
    subprocess.call(['dot', '-Tpng', f'./{outFile}.dot', '-o', f'{outFile}.png'])

  def copyTree(self):
    nodes = [self] + [i for i in self.optLeftRoot()]
    news = [Node() for i in range(len(nodes))]
    head = news[0]
    fc = True
    for i,n in enumerate(nodes):
      if fc:
        print(nodes[0], nodes[1])
        news[i].value = Token(n.value.tag, n.value.value)
        fc = False
      else:
        j = nodes.index(n.root)
        news[i].root = news[j]
      news[i].value = Token(n.value.tag, n.value.value)
      for node in n.nodes:
        j = nodes.index(node)
        news[i].add_node(news[j])
    h = Node()
    h.add_node(head)
    head = h
    return head

  def addEnd(self):
    tmp = Node(None, Token(CONCAT, '.'))
    ch = self.pop()
    tmp.add_node(ch)
    tmp.add(Token(END_MEAT, '\$'))
    self.add_node(tmp)

  def checkLeft(self):
    self.printTree()
    self.genDot("check.png")

  def prenullable(self):
    if self.value is None:
      return False
    if self.value.tag == META_NUM:
      # return False # True
      return True
    elif self.value.tag == CONCAT or self.value.tag == OR:
      return self.nodes[0].prenullable() and self.nodes[1].prenullable()
    elif self.value.tag == GROUP_BRACKET or self.value.tag == SQ_BRACKET:
      if self.nodes:
        return self.nodes[0].prenullable()
      else:
        return True
    else:
      return False

  def nullable(self):
    if self.nullables == -1:
      if self.prenullable():
        self.nullables = None
      else:
        if self.value.tag == EMPTY or self.value.tag == KLINI:
          self.nullables = True
        elif self.value.tag == OR:
          self.nullables = self.nodes[0].nullable() or self.nodes[1].nullable()
        elif self.value.tag == CONCAT:
          self.nullables = self.nodes[0].nullable() and self.nodes[1].nullable()
        elif self.value.tag == GROUP_BRACKET or self.value.tag == REPEATS or self.value.tag == SQ_BRACKET:
          self.nullables = self.nodes[0].nullable()
        else:
          self.nullables = False
    return self.nullables

  def firstpos(self):
    if self.firstposes == -1:
      if self.prenullable():
        self.firstposes = None
      else:
        if self.value.tag == EMPTY:
          self.firstposes = set()
        elif self.value.tag == KLINI:
          self.firstposes = self.nodes[0].firstpos()
        elif self.value.tag == OR:
          node0 = self.nodes[0].firstpos()
          node1 = self.nodes[1].firstpos()
          if node0 is None:
            self.firstposes = node1
          if node1 is None:
            self.firstposes = node0
          self.firstposes = node0 | node1 
        elif self.value.tag == CONCAT:
          node0 = self.nodes[0].firstpos()
          node1 = self.nodes[1].firstpos()
          if node0 is None:
            self.firstposes = node1
          if node1 is None:
            self.firstposes = node0
          if self.nodes[0].nullable():
            self.firstposes =  node0 | node1
          else:
            self.firstposes = node0
        elif self.value.tag == GROUP_BRACKET or self.value.tag == REPEATS or self.value.tag == SQ_BRACKET:
          # if self.prenullable():
          #   self.firstposes = None
          self.firstposes = self.nodes[0].firstpos()
        else:
          self.firstposes = set([id(self)])
    return self.firstposes

  def lastpos(self):
    if self.lastposes == -1:
      if self.prenullable():
        self.lastposes = None
      else:
        if self.value.tag == EMPTY:
          self.lastposes = set()
        elif self.value.tag == KLINI:
          self.lastposes = self.nodes[0].lastpos()
        elif self.value.tag == OR:
          node0 = self.nodes[0].lastpos()
          node1 = self.nodes[1].lastpos()
          if node0 is None:
            self.lastposes = node1
          if node1 is None:
            self.lastposes = node0
          self.lastposes =  node0 | node1 
        elif self.value.tag == CONCAT:
          node0 = self.nodes[0].lastpos()
          node1 = self.nodes[1].lastpos()
          if node0 is None:
            self.lastposes = node1
          if node1 is None:
            self.lastposes = node0
          if self.nodes[1].nullable():
            self.lastposes =  node0 | node1
          else:
            self.lastposes = node1
        elif self.value.tag == GROUP_BRACKET or self.value.tag == REPEATS or self.value.tag == SQ_BRACKET:
          # if self.prenullable():
          #   self.lastposes = None
          self.lastposes = self.nodes[0].lastpos()
        else:
          self.lastposes = set([id(self)])
    return self.lastposes


class SyntaxTree:
  root_stack: typing.List[Node]
  lexer: Lexer
  followposes: FollowPos
  root: Node
  root_null: Node
  ids: typing.Dict[int, Node]
  _functors = dict
  _joiner: Node
  _df_joiner: Node
  _groups_num: int
  _sq_num: int
  _OROR: list

  def __init__(self):
    self.lexer = Lexer()
    self._functors = {
      GROUP_BRACKET: self.op_group_brackets,
      SQ_BRACKET: self.op_sq_brackets,
      REPEATS: self.op_uno_left,
      OR: self.change_joiner,
      KLINI: self.op_uno_left,
      META: self.op_binary_join,
      META_NUM: self.op_meta_num,
      CHAR: self.op_binary_join,
      EMPTY: self.op_binary_join
    }
    self.clear()

  def __join(self, n1: Node, n2: Node, root: Node):
    self._joiner.add_node(n1)
    self._joiner.add_node(n2)
    root.add_node(self._joiner)
    self._joiner = self._df_joiner.copy()

  def __root_concat(self, n1: Node, n2: Node):
    if n1.isNotEmpty:
      ch = n1.pop()
      self.__join(ch, n2, n1)
    else:
      n1.add_node(n2)

  def _isOpenBracket(self, t: Token):
    return t.value in "(["

  def op_brackets(self, t: Token):
    if self._isOpenBracket(t):
      tmp = Node(None, t)
      self.__root_concat(self.root_stack[-1], tmp)
      self.root_stack.append(tmp)
      return None
    else:
      t2 = self.root_stack.pop()
      while t2.value.tag == TMP_TOKEN:
        troot = t2.root
        troot.pop()
        troot.add_node(t2.pop())
        t2 = self.root_stack.pop()
      return t2

  def op_group_brackets(self, t: Token):
    tmp = self.op_brackets(t)
    if tmp:
      self._OROR.pop()
      self._groups_num += 1
      tmp.value = Token(GROUP_BRACKET, f"gr_{self._groups_num}")
    else:
      self._OROR.append(self.root_stack[-1])
  
  def op_sq_brackets(self, t: Token):
    tmp = self.op_brackets(t)
    if self._df_joiner.value.tag == CONCAT:
      self._df_joiner = Node(None, Token(OR, '|'))
    else:
      self._df_joiner = Node(None, Token(CONCAT, '.'))
    self._joiner = self._df_joiner.copy()
    if tmp:
      self._sq_num += 1
      tmp.value = Token(SQ_BRACKET, f"sq_{self._sq_num}")
      if not tmp.nodes:
        tmp.add(Token(EMPTY, '#'))
      # root = tmp.root
      # root.nodes.remove(tmp)
      # root.add_node(tmp.pop())
    # else:
    #   self.op_binary_join(Token(EMPTY, '#'))

  def op_uno_left(self, t: Token):
    ch = self.root_stack[-1].pop()
    if ch.nodes:
      ch2 = ch.pop()
      tmp = ch.add(t)
      tmp.add_node(ch2)
      self.root_stack[-1].add_node(ch)
    else:
      tmp = self.root_stack[-1].add(t)
      tmp.add_node(ch)

  def op_binary_join(self, t: Token):
    tmp = self.root_stack[-1]
    if tmp.isNotEmpty:
      self.__join(tmp.pop(), Node(None, t), tmp)
    else:
      self.root_stack[-1].add(t)

  def op_meta_num(self, t: Token):
    val = int(t.value)
    if val > self._groups_num:
      raise PatternError('group index out off range')
    self.op_binary_join(Token(t.tag, t.value + '/'))

  def change_joiner(self, t: Token):
    if t.tag == OR:
      if self._OROR:
        n1 = self._OROR.pop()
        if n1.isNotEmpty:
          n2 = Node(None, Token(TMP_TOKEN, 'TMP'))
          ch = n1.pop()
          _joiner = Node(None, t)
          _joiner.add_node(ch)
          _joiner.add_node(n2)
          n1.add_node(_joiner)
          self.root_stack.append(n2)
          self._OROR.append(n2)
        
      else:
        n1 = self.root_stack[-1]
        if n1.isNotEmpty:
          n2 = Node(None, Token(TMP_TOKEN, 'TMP'))
          ch = n1.pop()
          _joiner = Node(None, t)
          _joiner.add_node(ch)
          _joiner.add_node(n2)
          n1.add_node(_joiner)
          self.root_stack.append(n2)
          self._OROR.append(_joiner)
        else:
          raise AttributeError("OR_TOKEN")

  def clear(self):
    self.root_stack = [Node()]
    self._df_joiner = Node(None, Token(CONCAT, '.'))
    self._joiner = self._df_joiner.copy()
    self._groups_num = 0
    self._sq_num = 0
    self.followposes = dict()
    self.ids = dict()
    self.root = None
    self._OROR = []
    self.lexer.clear()

  def build(self, s: str):
    gen = self.lexer.lex(s)
    for t in gen:
      self._functors[t.tag](t)

    if len(self.root_stack) > 1:
      raise PatternError("syntax tree")
    self.root_null = self.root_stack[0]
    self.root = self.root_stack[0].nodes[0]
    # self.addGroups()
    return self.root

  def __addFP(self, i: Node, s: typing.Set[Node]):
    if i in self.followposes:
      self.followposes[i] = (self.followposes[i] | s)
    else:
      self.followposes[i] = s

  def genFollowposes(self):
    root = self.root_stack[0].nodes[0]
    for n in root.optLeftRoot():
      self.ids[id(n)] = n
      n.firstpos()
      n.lastpos()
    
    for n in root.optLeftRoot():
      if n.value.tag == CONCAT: 
        for i in n.nodes[0].lastposes:
          self.__addFP(i, n.nodes[1].firstposes)
      elif n.value.tag == KLINI or n.value.tag == REPEATS: #or n.value.tag == GROUP_BRACKET 
        for i in n.nodes[0].lastposes:
          self.__addFP(i, n.firstposes)
    return self.followposes, self.ids      

  def _addGroups(self, groups: list, node):
    if node.value.tag == GROUP_BRACKET:
      groups.append(int(node.value.value[3:]))
    node.groups = groups
    for n in node.nodes:
      self._addGroups(groups.copy(), n)
  
  def addGroups(self):
    self._addGroups([], self.root)
    return self.root

if __name__ == '__main__':
  tree = SyntaxTree()
  # test = r"n[as\{]"
  # test = r"asd*((geg)[]([123\{\]]*)){3}"
  test = r"(12)|b"
  test = r"(a|b)*abb\$"
  test = r"(ba{5}){2}"
  test = r"[ab]{3}"
  test = r"[]"
  # test = r"ab{3}"
  test = r"(aba[abc]){3}\$"

  test = r"(na*)\1\$"
  # test = r"(aba(a|b|c)){3}\$"
  
  # test = r"(cab){3}"
  
  # test = r"(nana)|((n*[a]){3})"
  # test = r"(n[a])"
  # test = r"asd*(nad)|((cur\{))as[123]{6}[]\#\2"
  # test = r"a|b|c|([123456]*)"
  test = r"(a|b)*abb\#"
  # test = r"[123]"
  # test = r"(a|b)*abb\#\123123"
  # test = r"[]"
  test = r"xy|z*"
  test = r"(01)*|(10)*"
  test = r"abc*|deb[123]|kick|pick"
  # test = r"a*a(a[bc])*"
  treelist = tree.build(test)
  # treelist.printTree()

  tree.root_null.genDot()
  # print('check')
  # tree.root_null.checkLeft()
  # print('endcheck')
  # print(*tree.genFollowposes(), sep='\n\n')

  h = tree.root.nodes[0].nodes[1]
  print(h)
  h2 = h.copyTree()
  h2.addEnd()
  h2.genDot("graph2")
  # for k in tree.followposes:
  #   print(tree.ids[k])
  # for k in treelist.optLeftRoot():
  #   # print(tree.ids[k])
  #   print(k)
  #   print(k.firstpos(), k.lastpos(), sep='\t')
