# dhcli

Search delhaize.be products and edit your Delhaize cart from the terminal. Python 3, standard library only.

## Setup

```sh
uv tool install git+https://github.com/Triver1/delhaize-cli   # or: pipx install git+...
```

`cart` and `set` act on your own cart, so they need your login cookie. Copy the Cookie header of any request to `delhaize.be/api/v1/` from a logged-in browser (DevTools > Network > Request Headers) and add it to `~/.zshrc`:

```sh
export DELHAIZE_COOKIE='...'
```

The cookie expires when you log out of delhaize.be; copy it again then.

## Usage

```sh
dhcli search "lays pickles" -n 5         # no login needed
dhcli cart                               # cart lines and total at list price
dhcli set S2022072800600560098=5 ...     # set absolute quantities, 0 removes
```

## Tests

```sh
python3 test_delhaize.py
```
