from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QTextBrowser, QHBoxLayout, QVBoxLayout, QAction, QFileDialog
from PyQt5.Qt import *
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import *
import sys
from pyvis.network import Network
import webbrowser
from os.path import abspath

net = Network(notebook=True, directed=True)

GRAPH = []
from_m = []
to_m = []
graph_size = []
path = []
from_nodes = []
to_nodes = []
size = 0
k = 0
num = []

class Node:

    def __init__(self, data, indexloc = None):
        self.data = data
        self.index = indexloc


class Graph:

    @classmethod
    def create_from_nodes(self, nodes):
        return Graph(len(nodes), len(nodes), nodes)

    def __init__(self, row, col, nodes = None):
        # установка матрица смежности
        self.adj_mat = [[0] * col for _ in range(row)]
        self.nodes = nodes
        for i in range(len(self.nodes)):
            self.nodes[i].index = i

    # Связывает node1 с node2
    # Обратите внимание, что ряд - источник, а столбец - назначение
    # Обновлен для поддержки взвешенных ребер (поддержка алгоритма Дейкстры)
    def connect_dir(self, node1, node2, weight = 1):
        node1, node2 = self.get_index_from_node(node1), self.get_index_from_node(node2)
        self.adj_mat[node1][node2] = weight

    # Опциональный весовой аргумент для поддержки алгоритма Дейкстры
    def connect(self, node1, node2, weight = 1, path = 0):
        if path == 0:
            self.connect_dir(node1, node2, weight)
            self.connect_dir(node2, node1, weight)
        elif path == 1:
            self.connect_dir(node1, node2, weight)


    # Получает ряд узла, отметить ненулевые объекты с их узлами в массиве self.nodes
    # Выбирает любые ненулевые элементы, оставляя массив узлов
    # которые являются connections_to (для ориентированного графа)
    # Возвращает значение: массив кортежей (узел, вес)
    def connections_from(self, node):
        node = self.get_index_from_node(node)
        return [(self.nodes[col_num], self.adj_mat[node][col_num]) for col_num in range(len(self.adj_mat[node])) if self.adj_mat[node][col_num] != 0]

    # Проводит матрицу к столбцу узлов
    # Проводит любые ненулевые элементы узлу данного индекса ряда
    # Выбирает только ненулевые элементы
    # Обратите внимание, что для неориентированного графа
    # используется connections_to ИЛИ connections_from
    # Возвращает значение: массив кортежей (узел, вес)
    def connections_to(self, node):
        node = self.get_index_from_node(node)
        column = [row[node] for row in self.adj_mat]
        return [(self.nodes[row_num], column[row_num]) for row_num in range(len(column)) if column[row_num] != 0]


    def print_adj_mat(self):
        for row in self.adj_mat:
            print(row)

    def node(self, index):
        return self.nodes[index]


    def remove_conn(self, node1, node2):
        self.remove_conn_dir(node1, node2)
        self.remove_conn_dir(node2, node1)

    # Убирает связь в направленной манере (nod1 к node2)
    # Может принять номер индекса ИЛИ объект узла
    def remove_conn_dir(self, node1, node2):
        node1, node2 = self.get_index_from_node(node1), self.get_index_from_node(node2)
        self.adj_mat[node1][node2] = 0

        # Может пройти от node1 к node2
    def can_traverse_dir(self, node1, node2):
        node1, node2 = self.get_index_from_node(node1), self.get_index_from_node(node2)
        return self.adj_mat[node1][node2] != 0

    def has_conn(self, node1, node2):
        return self.can_traverse_dir(node1, node2) or self.can_traverse_dir(node2, node1)

    def add_node(self ,node):
        self.nodes.append(node)
        node.index = len(self.nodes) - 1
        for row in self.adj_mat:
            row.append(0)
        self.adj_mat.append([0] * (len(self.adj_mat) + 1))

    # Получает вес, представленный перемещением от n1
    # к n2. Принимает номера индексов ИЛИ объекты узлов
    def get_weight(self, n1, n2):
        node1, node2 = self.get_index_from_node(n1), self.get_index_from_node(n2)
        return self.adj_mat[node1][node2]

    # Разрешает проводить узлы ИЛИ индексы узлов
    def get_index_from_node(self, node):
        if not isinstance(node, Node) and not isinstance(node, int):
            raise ValueError("node must be an integer or a Node object")
        if isinstance(node, int):
            return node
        else:
            return node.index

    def dijkstra(self, node):
        # Получает индекс узла (или поддерживает передачу int)
        nodenum = self.get_index_from_node(node)
        # Заставляет массив отслеживать расстояние от одного до любого узла
        # в self.nodes. Инициализирует до бесконечности для всех узлов, кроме
        # начального узла, сохраняет "путь", связанный с расстоянием.
        # Индекс 0 = расстояние, индекс 1 = перескоки узла
        dist = [None] * len(self.nodes)
        for i in range(len(dist)):
            dist[i] = [float("inf")]
            dist[i].append([self.nodes[nodenum]])

        dist[nodenum][0] = 0
        # Добавляет в очередь все узлы графа
        # Отмечает целые числа в очереди, соответствующие индексам узла
        # локаций в массиве self.nodes
        queue = [i for i in range(len(self.nodes))]
        # Набор увиденных на данный момент номеров
        seen = set()
        while len(queue) > 0:
            # Получает узел в очереди, который еще не был рассмотрен
            # и который находится на кратчайшем расстоянии от источника
            min_dist = float("inf")
            min_node = None
            for n in queue:
                if dist[n][0] < min_dist and n not in seen:
                    min_dist = dist[n][0]
                    min_node = n

            # Добавляет мин. расстояние узла до увиденного, убирает очередь
            queue.remove(min_node)
            seen.add(min_node)
            # Получает все следующие перескоки
            connections = self.connections_from(min_node)
            # Для каждой связи обновляет путь и полное расстояние от
            # исходного узла, если полное расстояние меньше
            # чем текущее расстояние в массиве dist
            for (node, weight) in connections:
                tot_dist = weight + min_dist
                if tot_dist < dist[node.index][0]:
                    dist[node.index][0] = tot_dist
                    dist[node.index][1] = list(dist[min_node][1])
                    dist[node.index][1].append(node)
        return dist

class Dijkstra(QDialog):
    def __init__(self):
        super(Dijkstra, self).__init__()
        self.resize(300, 200)

        self.label_start = QLabel('Начала маршрута:', self)
        self.label_start.setGeometry(20, 100, 100, 20)

        self.line_start = QLineEdit(self)
        self.line_start.setGeometry(120, 100, 40, 20)

        self.label_end = QLabel('Конец маршрута:', self)
        self.label_end.setGeometry(20, 130, 100, 20)

        self.line_end = QLineEdit(self)
        self.line_end.setGeometry(120, 130, 40, 20)

        self.textB = QTextBrowser(self)
        self.textB.setOpenExternalLinks(True)
        self.textB.setStyleSheet('font-size: 15px')
        self.textB.setGeometry(20, 20, 260, 70)

        self.btn_start = QPushButton('Найти маршрут',self)
        self.btn_start.setGeometry(100, 160, 100, 30)



        self.btn_start.clicked.connect(self.Poisk)

    def Poisk(self):
        global size, k
        #if len(to_m) != 0:

            #graph = []
            #for i in range(size):
            #    graph.append(Node(f'{i}'))




        w_graph = Graph.create_from_nodes(GRAPH)
        print(-1)
        print(len(graph_size))
        print(k)
        for i in range(k):
            #print(from_m[i], to_m[i])
            w_graph.connect(from_m[i], to_m[i], graph_size[i], path[i])
        print(0)
        matrix = [(weight, [n.data for n in node]) for (weight, node) in w_graph.dijkstra(GRAPH[int(self.line_start.text())])]
        drow = None
        line = None
        print(1)
        print(matrix)

            # for i in range(len(matrix)):
            #     if int(self.line_end.text()) == matrix[i][1][len(matrix[i][1] - 1)]:
            #         for g in range(len(path)):
            #             if path[g] == 0:
            #                 matrix[i][1].insert(k, '<->')
            #                 k += 2
            #             elif path[g] == 1:
            #                 matrix[i][1].insert(k, '->')
            #                 k += 2
            #
            #         drow = ''.join(matrix[i][1])
            #         line = matrix[i][0]
            #         print(2)
            #         break

        for i in range(len(matrix)):
            for j in range(len(matrix[i][1])):
                if matrix[i][1][j] == self.line_end.text() and j == len(matrix[i][1]) - 1:
                    k = 1
                    print(matrix[i][1])
                    for g in range(len(path)):
                        if k>=len(matrix[i][1]):
                            break
                        # if matrix[i][1][k] == '->' or matrix[i][1][k] == '<->':
                        #     break
                        if path[g] == 0:
                            matrix[i][1].insert(k, '<->')


                        elif path[g] == 1:
                            matrix[i][1].insert(k, '->')

                        # if matrix[i][1][k] == '->':
                        #     break
                        print(100)
                        k+=2

                    print(200)
                    drow = ''.join(matrix[i][1])
                    line = matrix[i][0]
                    print(2)
                    break

        self.textB.moveCursor(QTextCursor.Start)
        self.textB.append(f'Маршрут: {drow}')
        self.textB.append(f'Длина маршрута: {line}')
        # else:
        #     # graph = []
        #     # for i in range(size):
        #     #    graph.append(Node(f'{i}'))
        #
        #     w_graph = Graph.create_from_nodes(GRAPH)
        #     print(-1)
        #     print(len(num[3]))
        #     print(k)
        #     for i in range(k):
        #         # print(from_m[i], to_m[i])
        #         w_graph.connect(int(num[1][i]), int(num[2][i]), int(num[3][i]), int(num[4][i]))
        #     print(0)
        #     matrix = [(weight, [n.data for n in node]) for (weight, node) in
        #               w_graph.dijkstra(GRAPH[int(self.line_start.text())])]
        #     drow = None
        #     line = None
        #     print(1)
        #     for i in range(len(matrix)):
        #         for j in matrix[i][1]:
        #             if j == self.line_end.text():
        #                 k = 1
        #                 for g in range(len(num[4])):
        #                     if int(num[4][g]) == 0:
        #                         matrix[i][1].insert(k, '<->')
        #                         k+=2
        #                     elif int(num[4][g]) == 1:
        #                         matrix[i][1].insert(k, '->')
        #                         k += 2
        #
        #                     if len(matrix[i][1]) < k - 1:
        #                         break
        #
        #                     # matrix[i][1].insert(k, '->')
        #                     # if matrix[i][1][k] == '->':
        #                     #     break
        #                     # k += 2
        #                     # if k > len(num[4]):
        #                     #     break
        #
        #                 drow = ''.join(matrix[i][1])
        #                 line = matrix[i][0]
        #                 print(2)
        #                 break

            # self.textB.moveCursor(QTextCursor.Start)
            # self.textB.append(f'Маршрут: {drow}')
            # self.textB.append(f'Длина маршрута: {line}')




class GraphWin(QDialog):
    def __init__(self):
        super(GraphWin, self).__init__()
        self.resize(450, 200)

        self.cb = QCheckBox('Ориентриванное ребро', self)
        self.cb.move(20, 20)


        self.lbl_start_point = QLabel('Начальная вершина:',self)
        self.lbl_start_point.setGeometry(20, 40, 150, 20)

        self.line_strat_poit = QLineEdit(self)
        self.line_strat_poit.setGeometry(130, 40, 40, 20)

        self.lbl_end_point = QLabel('Конечная вершина:', self)
        self.lbl_end_point.setGeometry(20, 65, 150, 20)

        self.line_end_poit = QLineEdit(self)
        self.line_end_poit.setGeometry(130, 65, 40, 20)

        self.lbl_size = QLabel('Размер ребра:', self)
        self.lbl_size.setGeometry(20, 90, 150, 20)

        self.line_size = QLineEdit(self)
        self.line_size.setGeometry(130, 90, 40, 20)

        self.tb = QTextBrowser(self)
        self.tb.setOpenExternalLinks(True)
        self.tb.setStyleSheet('font-size: 15px')
        self.tb.setGeometry(190, 20, 240, 160)

        self.tb.append('Наименование вершин начинается с 0\n')

        self.btn_next = QPushButton('Добавить граф', self)
        self.btn_next.setGeometry(20, 130, 150, 20)

        self.btn_start = QPushButton('Создать граф', self)
        self.btn_start.setGeometry(20, 160, 150, 20)

        self.dij = Dijkstra()

        self.btn_next.clicked.connect(self.NextPath)

        self.btn_start.clicked.connect(self.Start)

    def NextPath(self):
        global k
        start = int(self.line_strat_poit.text())
        stop = int(self.line_end_poit.text())
        line = int(self.line_size.text())

        if self.cb.isChecked() == True:
            path.append(1)
        else:
            path.append(0)
        #if start > 0:
        from_m.append(start)
        to_m.append(stop)

        from_nodes.append(GRAPH[start])
        to_nodes.append(GRAPH[stop])
        graph_size.append(line)

        path_from_to = []
        path_from_to.append(str(start))
        path_from_to.append(str(stop))
        if self.cb.isChecked():
            print_tb = '->'.join(path_from_to) + f'\t{line}'
        else:
            print_tb = '<->'.join(path_from_to) + f'\t{line}'

        self.tb.moveCursor(QTextCursor.Start)
        self.tb.append(print_tb)
        k+=1
        #else:
        #    self.tb.moveCursor(QTextCursor.Start)
        #    self.tb.append('Вершина графа должна быть больше 0')

        self.line_size.clear()
        self.line_end_poit.clear()
        self.line_strat_poit.clear()
        self.cb.setChecked(False)


    def Start(self):
        for i in range(len(to_m)):
            if path[i] == 0:
                net.add_edge(to_m[i], from_m[i], weight=100, title=f'{graph_size[i]}')
                net.add_edge(from_m[i], to_m[i], weight=100, title=f'{graph_size[i]}')

            elif path[i] == 1:
                net.add_edge(from_m[i], to_m[i], weight=100, title=f'{graph_size[i]}')


        net.repulsion(node_distance=150, spring_length=100)
        net.show_buttons(filter_=True)
        net.show('mygraph.html')

        webbrowser.open('mygraph.html', new=1)
        
        self.close()
        self.dij.exec_()

class FirsteWin(QWidget):
    def __init__(self):
        super(FirsteWin, self).__init__()
        self.resize(400, 180)

        self.cb_f = QCheckBox('Чтение файла', self)
        self.cb_f.setChecked(True)

        self.cb_f.move(30, 20)

        self.cb_r = QCheckBox('Ручной ввод', self)
        self.cb_r.move(30, 70)

        self.label_path = QLabel('Введите название файла с расширением:', self)
        self.label_path.setGeometry(30, 40, 220, 20)
        # self.line_path = QLineEdit(self)
        # self.line_path.setGeometry(250, 40, 120, 20)
        self.pathFileName = QPushButton('Открыть файл', self)
        self.pathFileName.setGeometry(250, 40, 140, 30)

        self.label_size_graph = QLabel('Введите количество вершин графа:', self)
        self.label_size_graph.setGeometry(30, 90, 200, 20)

        self.line_size_graph = QLineEdit(self)
        self.line_size_graph.setGeometry(250, 90, 40, 20)
        self.line_size_graph.setEnabled(False)

        self.btn_size_graph = QPushButton('Задать количество', self)
        self.btn_size_graph.setGeometry(130, 120, 140, 30)
        self.btn_size_graph.setEnabled(False)

        self.gr = GraphWin()
        self.poisk = Dijkstra()
        self.cb_f.stateChanged.connect(self.Change1)
        self.cb_r.stateChanged.connect(self.Change1)
        self.btn_size_graph.clicked.connect(self.Size)
        self.pathFileName.clicked.connect(self.ReadFile)

    def Change1(self, state):
        if state == Qt.Checked:
            if self.sender() == self.cb_f:
                self.cb_r.setChecked(False)
                self.line_size_graph.setEnabled(False)
                self.pathFileName.setEnabled(True)
                self.btn_size_graph.setEnabled(False)
            elif self.sender() == self.cb_r:
                self.cb_f.setChecked(False)
                self.pathFileName.setEnabled(False)
                self.line_size_graph.setEnabled(True)
                self.btn_size_graph.setEnabled(True)

    def Size(self):
        global size
        size = int(self.line_size_graph.text())
        for i in range(size):
            GRAPH.append(Node(f'{i}'))
            net.add_node(i, label=f'{i}')

        self.close()
        self.gr.exec_()

    def RStart(self):
        global size, k

        size = int(num[0][0])
        k = len(num[1])
        for i in range(size):
            GRAPH.append(Node(f'{i}'))
            net.add_node(i, label=f'{i}')
        for i in range(len(num[4])):
            if int(num[4][i]) == 0:
                net.add_edge(int(num[2][i]), int(num[1][i]), weight=100, title=f'{num[3][i]}')
                net.add_edge(int(num[1][i]), int(num[2][i]), weight=100, title=f'{num[3][i]}')
            elif int(num[4][i]) == 1:
                net.add_edge(int(num[1][i]), int(num[2][i]), weight=100, title=f'{num[3][i]}')



        net.repulsion(node_distance=150, spring_length=100)
        net.show_buttons(filter_=True)
        net.show('mygraph.html')

        webbrowser.open('mygraph.html', new=1)
        self.close()
        self.poisk.exec_()



    def ReadFile(self):
        global size
        res = QFileDialog.getOpenFileName(self, '', 'C:/', 'Text files (*.txt)')
        path1 = res[0]
        mass = []
        with open(path1, 'r') as f:
            a = f.readlines()
        for i in range(len(a)):
            s = a[i].split(': ')
            mass.append(s)
        print(mass)
        l = []
        for i in range(len(mass)):
            l.append(mass[i][1])
        print(l)
        l = [line.rstrip() for line in l]
        for i in range(len(l)):
            num.append(l[i].split())
        print(num)
        for i in num[1]:
            from_m.append(int(i))
        print(from_m)
        for i in num[2]:
            to_m.append(int(i))
        for i in num[3]:
            graph_size.append(int(i))
        for i in num[4]:
            path.append(int(i))
        self.RStart()



if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = FirsteWin()
    w.show()
    sys.exit(app.exec_())
