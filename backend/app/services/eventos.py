"""
Puente entre el orquestador (que corre en threads, un thread por segmento) y el
endpoint SSE que consume el frontend. El orquestador ya imprime su progreso
por consola (print) para uso por CLI — EmisorEventos añade el mismo progreso
a una cola thread-safe, sin quitarle nada al CLI.
"""

import queue


class EmisorEventos:
    def __init__(self):
        self._cola: queue.Queue = queue.Queue()

    def emitir(self, tipo: str, **data):
        self._cola.put({"tipo": tipo, **data})

    def cerrar(self):
        self._cola.put(None)

    def eventos(self):
        """Generador bloqueante — consumido por el endpoint SSE en el thread principal."""
        while True:
            item = self._cola.get()
            if item is None:
                return
            yield item
