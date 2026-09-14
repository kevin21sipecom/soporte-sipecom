import unittest

from soporte_sipecom.conversations import (
    chats_root,
    delete_thread,
    load_index,
    new_id,
    save_thread,
)


class DeleteThreadTests(unittest.TestCase):
    def test_delete_removes_index_and_dir(self):
        cid = f"test-{new_id()}"
        save_thread(cid, [{"role": "user", "content": "hola"}], [], "p")
        self.assertTrue((chats_root() / cid / "thread.json").is_file())
        delete_thread(cid)
        self.assertFalse((chats_root() / cid).exists())
        self.assertTrue(all(str(x.get("id") or "") != cid for x in load_index()))


if __name__ == "__main__":
    unittest.main()
