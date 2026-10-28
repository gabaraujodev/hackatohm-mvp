import tempfile
import unittest
from pathlib import Path
import server

class Tests(unittest.TestCase):
    def test_limites_apenas_demo(self):
        self.assertEqual(server.status(42, 29), 'normal')
        self.assertEqual(server.status(70, 29), 'atencao')
        self.assertEqual(server.status(85, 29), 'critico')
    def test_banco_simulado(self):
        original=server.DB
        try:
            with tempfile.TemporaryDirectory() as folder:
                server.DB=Path(folder)/'teste.sqlite3'
                server.init_db()
                overview=server.overview()
                self.assertEqual(len(overview['escovas']), 4)
                self.assertEqual(overview['amostras'],100)
                r=server.add_reading({'escova':'E06','temperatura_c':45.5,'ambiente_c':28.0})
                self.assertEqual(r['estado'],'normal')
                self.assertEqual(len(server.overview()['escovas']),5)
        finally:
            server.DB=original

if __name__ == '__main__':unittest.main()
