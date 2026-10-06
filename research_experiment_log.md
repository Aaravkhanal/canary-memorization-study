# Research Experiment Log

This file will accumulate the outputs of each evaluation script in order.

---
Traceback (most recent call last):
  File "/Users/aaravkhanal/Desktop/myllm/canary-memorization-study/scripts/eval_memorization.py", line 206, in <module>
    main()
    ~~~~^^
  File "/Users/aaravkhanal/Desktop/myllm/canary-memorization-study/scripts/eval_memorization.py", line 175, in main
    engine = load_engine(args.checkpoint, args.tokenizer, args.device)
  File "/Users/aaravkhanal/Desktop/myllm/canary-memorization-study/scripts/eval_memorization.py", line 47, in load_engine
    return InferenceEngine.from_checkpoint(checkpoint, tokenizer_dir, device)
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/aaravkhanal/Desktop/myllm/aarav-lm/src/aarav_lm/inference/engine.py", line 193, in from_checkpoint
    tok = AaravTokenizer.load(tokenizer_dir)
  File "/Users/aaravkhanal/Desktop/myllm/aarav-lm/src/aarav_lm/tokenizer/bpe.py", line 111, in load
    raw = (d / "tokenizer.json").read_text(encoding="utf-8")
  File "/Users/aaravkhanal/miniforge3/lib/python3.13/pathlib/_local.py", line 546, in read_text
    return PathBase.read_text(self, encoding, errors, newline)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/aaravkhanal/miniforge3/lib/python3.13/pathlib/_abc.py", line 632, in read_text
    with self.open(mode='r', encoding=encoding, errors=errors, newline=newline) as f:
         ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/aaravkhanal/miniforge3/lib/python3.13/pathlib/_local.py", line 537, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'artifacts/tokenizer_dir/tokenizer.json'
