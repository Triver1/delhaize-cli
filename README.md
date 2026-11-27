# delhaize-cli

Search delhaize.be products and edit your Delhaize cart from the terminal. Python 3, standard library only.

```sh
./delhaize.py search "lays pickles" -n 5        # no login needed
./delhaize.py cart                              # list cart lines and the total at list price
./delhaize.py set S2022072800600560098=5 ...    # set absolute quantities, 0 removes
```

`cart` and `set` need `DELHAIZE_COOKIE`: the Cookie header of a request to `delhaize.be/api/v1/` from a logged-in browser (DevTools > Network > Request Headers).

Tests: `python3 test_delhaize.py`
