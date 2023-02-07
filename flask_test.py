import os
from unittest import TestCase, main
from api.endpoints import ModelRemove


class TestModelRemove(TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ['TEST'] = '1'

    def test_get(self):
        remover = ModelRemove()
        ans = remover.post('neuralNetwork')
        self.assertEqual(ans[0]["status"], "Failed")
        self.assertEqual(ans[1], 408)
            

if __name__ == '__main__':
    main()