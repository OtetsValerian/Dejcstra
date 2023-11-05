from pyvis.network import Network
import webbrowser



size = int(input("Введите количество вершин: "))

net = Network(notebook =True, directed =True)
for i in range(size):
    net.add_node(i, label=f'{i}')

while True:
    start = input('С какой вершины? ')
    if start == 'stop':
        break
    stop = int(input('До какой вершины? '))
    line = int(input('Длинны грани: '))
    path = int(input('Ориентриваонный граф? '))
    if path == 0:
        net.add_edge(int(start), stop, weight=10, title=f'{line}')
        net.add_edge(stop, int(start), weight=10, title=f'{line}')
    if path == 1:
        net.add_edge(int(start), stop, weight=10, title=f'{line}')


net.repulsion(node_distance=150, spring_length=100)
net.show_buttons(filter_=True)

net.show('mygraph.html')

webbrowser.open('mygraph.html', new=1)
