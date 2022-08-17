  $ export PYTHONPATH="$TESTDIR:$PYTHONPATH"
A basic example
  $ echo '(print 1)' | python -m compile && java -cp . MyClass
  1
