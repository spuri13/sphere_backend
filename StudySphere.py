

class Queue:
  def __init__(self):
    self.queue = []

  def getQueue(self):
    return self.queue
    
  def enqueue(self, element):
    self.queue.append(element)

  def dequeue(self):
    if self.isEmpty():
      return "Queue is empty"
    return self.queue.pop(0)

  def peek(self):
    if self.isEmpty():
      return "Queue is empty"
    return self.queue[0]

  def isEmpty(self):
    return len(self.queue) == 0

  def size(self):
    return len(self.queue)

class Node:
    def __init__(self, name ):
        self.name = name 
        self.children = []
        self.visited = False

    def __str__(self):
        return self.name

a = Node("A")
b = Node("B")
c = Node("C")
d = Node("C")
a.children = [b, c]
b.children = [d]

q = Queue()

q.enqueue(a)
print(q.getQueue()[0])
while not q.isEmpty():
    cnode = q.dequeue()
    print("Dequeued:", cnode.name)
    for child in cnode.children:
       if not child.visited == True:
          child.visited = True
          q.enqueue(child)
print("Current queue:", [n.name for n in q.getQueue()])


    







        