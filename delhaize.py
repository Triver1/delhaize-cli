#!/usr/bin/env python3
"""Delhaize.be CLI: search products, show ingredients and nutrients, show the cart, set cart quantities.

Cart commands need DELHAIZE_COOKIE: the Cookie header of a request to delhaize.be/api/v1/
from a logged-in browser (DevTools > Network > Request Headers).
"""
import argparse
import html
import json
import os
import sys
import urllib.request

API = "https://www.delhaize.be/api/v1/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0 Safari/537.36"

SEARCH = """query GetProductSearch($lang:String $searchQuery:String $pageSize:Int $fields:String){
  productSearch:productSearchV2(lang:$lang searchQuery:$searchQuery pageSize:$pageSize fields:$fields){
    products{code name manufacturerName price{value supplementaryPriceLabel2} stock{inStock}}}}"""
CART = """query Cart($lang:String!){cart(lang:$lang){totalUnitCount
  entries{quantity product{code name manufacturerName price{value supplementaryPriceLabel2}}}}}"""
PRODUCT = """query ProductDetails($productCode:String! $lang:String!){productDetails(productCode:$productCode lang:$lang){
  name manufacturerName wsNutriFactData{ingredients nutrients{nutrients{id valueList{value}}}}}}"""
UPDATE = """mutation MiniBasketUpdateCartEntryQuantity($lang:String! $entries:[EntryInput!]!){
  cart:updateCartEntryQuantity(entries:$entries lang:$lang){totalQuantity}}"""


def gql(op, query, variables, auth=False):
    headers = {"content-type": "application/json", "x-apollo-operation-name": op, "user-agent": UA}
    if auth:
        if not os.environ.get("DELHAIZE_COOKIE"):
            sys.exit("DELHAIZE_COOKIE is not set (see Setup in the README)")
        headers["cookie"] = os.environ["DELHAIZE_COOKIE"]
    body = json.dumps({"operationName": op, "query": query, "variables": {"lang": "nl", **variables}}).encode()
    with urllib.request.urlopen(urllib.request.Request(API, body, headers), timeout=30) as r:
        data = json.load(r)
    if data.get("errors"):
        sys.exit("; ".join(e["message"] for e in data["errors"]))
    return data["data"]


def label(p):
    return " ".join(filter(None, [p["manufacturerName"], p["name"], p["price"]["supplementaryPriceLabel2"]]))


def deltas(current, targets):
    return [{"productCode": c, "quantityDelta": str(q - current.get(c, 0))} for c, q in targets.items() if q != current.get(c, 0)]


def get_cart():
    return gql("Cart", CART, {}, auth=True)["cart"]


def print_cart(cart):
    for e in cart["entries"]:
        p = e["product"]
        print(f"{e['quantity']:>4} x {p['code']}  €{e['quantity'] * p['price']['value']:>7.2f}  {label(p)}")
    # the API's totalPrice is stale until the cart page recalculates it, so sum the lines instead
    total = sum(e["quantity"] * e["product"]["price"]["value"] for e in cart["entries"])
    print(f"{cart['totalUnitCount']} items, €{total:.2f} at list price (promotions apply at checkout)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search", help="search products (no login needed)")
    s.add_argument("query")
    s.add_argument("-n", type=int, default=10)
    for name, text in [("ingredients", "show the ingredient list"), ("nutrients", "show nutrients per 100 g/ml")]:
        sub.add_parser(name, help=f"{text} of products (no login needed)").add_argument("codes", nargs="+", metavar="CODE")
    sub.add_parser("cart", help="show the cart")
    st = sub.add_parser("set", help="set absolute quantities: CODE=QTY ... (0 removes)")
    st.add_argument("items", nargs="+", metavar="CODE=QTY")
    a = ap.parse_args()

    if a.cmd == "search":
        for p in gql("GetProductSearch", SEARCH, {"searchQuery": a.query, "pageSize": a.n, "fields": "PRODUCT_TILE"})["productSearch"]["products"]:
            stock = "" if (p["stock"] or {}).get("inStock") else "  OUT OF STOCK"
            print(f"{p['code']}  €{p['price']['value']:>6.2f}  {label(p)}{stock}")
    elif a.cmd in ("ingredients", "nutrients"):
        for code in a.codes:
            p = gql("ProductDetails", PRODUCT, {"productCode": code})["productDetails"]
            if not p:
                sys.exit(f"unknown product {code}")
            facts = p["wsNutriFactData"] or {}
            print(" ".join(filter(None, [p["manufacturerName"], p["name"], f"({code})"])))
            if a.cmd == "ingredients":
                print(html.unescape(facts.get("ingredients") or "no ingredient list"))
            else:
                for table in facts.get("nutrients") or []:
                    for n in table["nutrients"]:
                        print(f"  {n['id']}: {', '.join(v['value'] for v in n['valueList'])}")
            print()
    elif a.cmd == "cart":
        print_cart(get_cart())
    else:
        targets = {}
        for item in a.items:
            code, _, qty = item.partition("=")
            if not qty.isdigit():
                sys.exit(f"bad item {item!r}, expected CODE=QTY")
            targets[code] = int(qty)
        current = {e["product"]["code"]: e["quantity"] for e in get_cart()["entries"]}
        changes = deltas(current, targets)
        if changes:
            gql("MiniBasketUpdateCartEntryQuantity", UPDATE, {"entries": changes}, auth=True)
        print_cart(get_cart())


if __name__ == "__main__":
    main()
