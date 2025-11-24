# Implementación de Estructuras de Datos y Algoritmos Optimizados en Entornos Distribuidos (Python y Nube)
## Introducción

En esta clase revisaremos las estructuras de datos fundamentales (listas, árboles, grafos, colas) y los algoritmos de búsqueda y ordenación clásicos, implementándolos en Python de forma eficiente. Además, exploraremos cómo optimizar la manipulación de datos en entornos distribuidos y aplicaciones en la nube. Se abordará la implementación desde cero (creando nuestras propias clases), para luego usar las estructuras y algoritmos proporcionados por Python, analizando su complejidad. Finalmente, veremos ejemplos prácticos de cómo aplicar algoritmos de búsqueda y ordenación en la nube (AWS, Azure, GCP), incluyendo acceso a storages en cada plataforma y uso de funciones serverless para ejecutar código en la nube. El nivel de la sesión es de Maestría, por lo que profundizaremos en eficiencia y buenas prácticas.

## Estructuras de Datos Fundamentales en Python
### Listas (Arrays Dinámicos)

Una lista en Python es una secuencia ordenada y mutable de elementos. Internamente, las listas de Python se implementan como arrays dinámicos, es decir, un bloque contiguo de memoria que puede redimensionarse según se agreguen elementos. Esto permite acceder o modificar cualquier elemento mediante índice. Las operaciones de inserción o eliminación al final de la lista son muy eficientes. Sin embargo, insertar o remover elementos al inicio o mitad de una lista es costoso, ya que se debe desplazar el resto de elementos en memoria. A nivel de implementación, cuando una lista se queda sin espacio, Python automáticamente realoca un array más grande y copia los elementos.

En Python podemos implementar desde cero una lista dinámica para entender el proceso. Por ejemplo, usando una clase que internamente use un array de la librería estándar array o la propia lista de Python como buffer. Sin embargo, normalmente usaremos la clase built-in list de Python, que ya está optimizada en C. A continuación, se muestra un simple ejemplo de implementación de un array dinámico en Python para ilustrar la idea de redimensionamiento:

```Python
class DynamicArray:  
    def __init__(self):
        self.capacity = 1  # capacidad inicial
        self.length = 0    # elementos actuales
        self.data = [None] * self.capacity

    def append(self, value):
        # si está lleno, realocar con el doble de capacidad
        if self.length == self.capacity:
            self._resize(2 * self.capacity)
        self.data[self.length] = value
        self.length += 1

    def _resize(self, new_cap):
        new_data = [None] * new_cap
        for i in range(self.length):
            new_data[i] = self.data[i]
        self.data = new_data
        self.capacity = new_cap

# Uso de DynamicArray
arr = DynamicArray()
for i in range(5):
    arr.append(i)
print(arr.data, arr.length, arr.capacity)  # [0, 1, 2, 3, 4, None, None, None] 5 8

```

En este ejemplo, nuestro DynamicArray duplica su capacidad cuando se llena. Python hace algo similar de manera eficiente en C: por eso list.append tiende a ser muy rápido en promedio. Una vez entendida la implementación, en aplicaciones reales se utiliza directamente list de Python, aprovechando sus operaciones optimizadas. En resumen, las listas nos proporcionan versatilidad para almacenar colecciones y permiten: acceso indexado rápido, añadir/remover al final eficientemente, pero no son ideales para inserciones/eliminaciones frecuentes al comienzo (donde conviene usar otras estructuras, como veremos con las colas).

### Árboles (Ejemplo: Árbol Binario de Búsqueda)

Un árbol es una estructura de datos jerárquica compuesta por nodos con una relación padre-hijo. En particular, un árbol binario de búsqueda (BST) es un tipo de árbol binario donde cada nodo tiene a lo sumo dos hijos (izquierdo y derecho), y se cumple que los valores del subárbol izquierdo son menores al valor del nodo, y los del subárbol derecho son mayores. Esta propiedad ordenada permite búsquedas eficientes: en un BST balanceado, buscar un elemento tiene complejidad promedio O(log n), ya que se descarta la mitad del árbol en cada comparación. Sin embargo, en el peor caso (por ejemplo, si el árbol se “degenere” en una lista enlazada por inserciones ordenadas) la búsqueda puede ser O(n). Además de búsqueda, los BST soportan inserción y eliminación en tiempo O(log n) promedio.

![alt text](image-1.png)

Figura: Ejemplo de un árbol binario de búsqueda de 9 nodos y profundidad 3, con 8 en la raíz
en.wikipedia.org
. Cada nodo a la izquierda tiene un valor menor, y a la derecha un valor mayor que la raíz, manteniendo orden para búsqueda eficiente
en.wikipedia.org
. En un BST balanceado, operaciones de búsqueda, inserción y eliminación son O(log n) en promedio, aunque en el peor caso degenerado podrían caer a O(n)
en.wikipedia.org
.

Para implementar desde cero un árbol binario en Python, definimos una clase Node con atributos para el valor y punteros a sus hijos, y funciones para insertar o buscar elementos recursivamente. Por ejemplo: