from django.shortcuts import render
from .stonksapi import get_investor, get_leaderboard, get_offers, make_sell_offer, retract_sell_offer, buy_stocks
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json

# Create your views here.
def investors(request, investor):
    result = get_investor(investor)
    print("investor received")
    return HttpResponse(json.dumps(result))

@csrf_exempt
def offers(request):
    if request.method == "GET":
        result = get_offers()
        print("offers received")
        return HttpResponse(json.dumps(result))

    if request.method == "POST":
        params = request.POST
        if len(params.keys()) != 4:
            return HttpResponseBadRequest("bad")
        make_sell_offer(params["seller"], params["stock"], float(params["price"]), float(params["maximum"]))
        print("offer made")
        return HttpResponse("Offer successful")

    if request.method == "DELETE":
        breakpoint()
        params = request.read()
        buy_stocks(params["seller"], params["stock"])
        print("offer retracted")
        return HttpsResponse("Stock retracted successfully")

def leaderboard(request):
    result = get_leaderboard()
    print("leaderboard received")
    return HttpResponse(json.dumps(result))

@csrf_exempt
def buy(request):
    if request.method == "POST":
        params = request.POST
        if len(params.keys()) != 3:
            return HttpResponseBadRequest("bad")
        buy_stocks(params['buyer'], params['stock'], float(params['value']))
        print("stock bought")
        return HttpResponse("Stock bought successfully")
