from django.core.exceptions import FieldDoesNotExist
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from django.contrib.auth import logout as do_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import *
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect
from rest_framework import status, request
from rest_framework.decorators import api_view
from rest_framework.response import Response
from Exceptions import NoContingut
from GeoInfoSystem.models import *
from GeoInfoSystem.serializers import *
from Exceptions import *
from django.core import serializers
import json
import re
import random
import urllib.parse
# Create your views here.
###################################################################
# API PER ALS PUNTS D'INTERÈS.                                    #
###################################################################
"""
GET /v1/geoInfoSystem/allPuntsInteres/
Aquest mètode retorna tots els punts d'interes que hi ha presents en la base de dades.
Retorna 200 OK i la informació demanada, altre cas retorna un 404 NOT FOUND, en senyal que no troba cap.
"""
@api_view(['GET',])
def getPuntsInteres(request):
    if request.method == 'GET':
        try:
            puntsInteres = puntInteres.objects.all()
            if not puntsInteres:
                raise NoContingut
            serializer = puntInteresSerializer(puntsInteres, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha Punts d\'interès.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/puntInteresByCity/?ciutat=c
Aquest mètode retorna el/s punt/s d'interès que hi hagi en la determinada ciutat "c". 
Retorna un 400 BAD REQUEST en cas que no hi hagi el query param "ciutat". En cas que tot estigui bé retorna un 200 OK
amb les dades demanades. En altre cas retorna un 404 NOT FOUND informant que no hi ha cap informació.
"""
@api_view(['GET',])
def getPuntInteresByCity(request):
    if request.method == 'GET':
        try:
            localitat=request.query_params.get('ciutat')
            if not localitat:
                return Response('Falta el parametre ciutat per a poder executar la operació.', status=status.HTTP_400_BAD_REQUEST)
            puntsInteres = puntInteres.objects.all().filter(localitat=localitat)
            if not puntsInteres:
                raise NoContingut
            serializer = puntInteresSerializer(puntsInteres, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha Punts d\'interès.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/puntInteresByCoordenades/?latitud=0&longitud=0
Aquest mètode retorna el punt d'interès que hi ha ubicat en la latitud=0 i longitud=0. En cas que falti algun dels dos
paràmetre retorna un 400 BAD REQUEST. En cas que no trobi cap punt d'interès en aquelles coordenades retorna un 404 NOT FOUND.
En altre cas retorna un 200 OK amb la informació demanada.
"""
@api_view(['GET',])
def getPuntInteresEspecific(request):
    if request.method == 'GET':
        try:
            latitud=request.query_params.get('latitud')
            longitud=request.query_params.get('longitud')
            if not latitud or not longitud:
                return Response('Falten la latitud i/o la longitud per a poder executar la operació.', status=status.HTTP_400_BAD_REQUEST)
            puntInteresCercat= puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
            if not puntInteresCercat:
                raise NoContingut
            serializer = puntInteresSerializer(puntInteresCercat, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No s\'ha trobat cap punt d\'interes en aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)

"""
PUT /v1/geoInfoSystem/updatePuntInteres/<latitud>/<longitud>/
Aquest mètode actualitza la informació del punt d'interes situat en la latitud=<latitud>, longitud=<longitud>.
Comprova que els elements que conformen el cos del missatge HTTP siguin correctes, en altre cas retorna un 400 BAD REQUEST,
juntament amb no passar-li la latitud o la longitud o bé si el cos del missatge és buit.
En altre cas, si tot s'ha fet correctament retorna un 200 OK i rebota el punt d'interes actualitzat.
"""
@api_view(['PUT',])
def updatePuntInteres(request, latitud, longitud):
    #per tal de fer un update real en el camp primer el que s'ha de fer es: model.objects.all().filter(filtre_per_quedarnos_amb_1).update(field1=newvalue1, field2=newvalue2, ...)
    if request.method == 'PUT':
        if not request.body:
            return Response('Falta passar-li informacio al cos del missatge.', status=status.HTTP_400_BAD_REQUEST)
        if not latitud or not longitud:
            return Response('Falten la latitud i/o la longitud per a poder executar la operació.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded=request.body.decode('utf-8')
        body=json.loads(body_decoded) #json data #get info --> value=body["key"]
        keys=body.keys()
        errorsInEntryJSON=""
        for key in keys:
            try:
                puntInteres._meta.get_field(key)
            except FieldDoesNotExist:
                errorsInEntryJSON=errorsInEntryJSON+'['+str(key)+"] no es un camp correcte."
        if errorsInEntryJSON:
            errorsInEntryJSON=errorsInEntryJSON+'Revisa els camps i torna executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        try:
            puntInteresCercat = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
            if not puntInteresCercat:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No s\'ha trobat cap punt d\'interes en les coordenades ['+str(latitud)+','+str(longitud)+']', status=status.HTTP_404_NOT_FOUND)
        #No hi ha error en les dades dentrada
        latitudModificada=False
        longitudModificada=False
        novaLatitud=0.0
        novaLongitud=0.0
        for key in keys:
            if key == 'latitud':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(latitud=body[key])
                latitudModificada=True
                novaLatitud=body[key]
            elif key == 'longitud':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(longitud=body[key])
                longitudModificada=True
                novaLongitud=body[key]
            elif key == 'idMapa':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(idMapa=body[key])
            elif key == 'tipus':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(tipus=body[key])
            elif key == 'actiu':
                if body[key] == 'True' or body[key] == 1:
                    actiu=True
                else:
                    actiu=False
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(actiu=actiu)
            elif key == 'superficie':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(superficie=body[key])
            elif key == 'localitat':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(localitat=body[key])
            elif key == 'pais':
                puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).update(pais=body[key])


        puntInteresCercat = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
        if latitudModificada and longitudModificada:
            puntInteresCercat = puntInteres.objects.all().filter(latitud=novaLatitud, longitud=novaLongitud)
        elif latitudModificada and not longitudModificada:
            puntInteresCercat = puntInteres.objects.all().filter(latitud=novaLatitud, longitud=longitud)
        elif longitudModificada and not latitudModificada:
            puntInteresCercat = puntInteres.objects.all().filter(latitud=latitud, longitud=novaLongitud)


        serializer = puntInteresSerializer(puntInteresCercat, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

"""
POST /v1/geoInfoSystem/newPuntInteres/
Aquest mètode genera un nou punt d'interès. Retorna un 400 BAD REQUEST en cas que no hi hagi cos de missatge en el HTTP POST.
En cas que hi hagi algun parametre que no sigui de punt d'interes també retorna un 400 BAD REQUEST i un string informat del que hi ha malament.
En altre cas retorna un 201 CREATED i rebota l'element generat.
"""
@api_view(['POST',])
def postNewPuntInteres(request):
    if request.method == 'POST':
        if not request.body:
            return Response('Falta passar-li informacio al cos del missatge.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded = request.body.decode('utf-8')
        body = json.loads(body_decoded)  # json data #get info --> value=body["key"]
        keys = body.keys()
        errorsInEntryJSON = ""
        for key in keys:
            try:
                puntInteres._meta.get_field(key)
            except FieldDoesNotExist:
                errorsInEntryJSON = errorsInEntryJSON + '[' + str(key) + "] no es un camp correcte."
        if errorsInEntryJSON:
            errorsInEntryJSON = errorsInEntryJSON + 'Revisa els camps i torna executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        latitud=0.0
        longitud=0.0
        idMapa=1
        tipus=""
        actiu=False
        superficie=0.0
        localitat=""
        pais=""
        for key in keys:
            if key == 'latitud':
                latitud=body[key]
            elif key == 'longitud':
                longitud=body[key]
            elif key == 'idMapa':
                idMapa=body[key]
            elif key == 'tipus':
                tipus=body[key]
            elif key == 'actiu':
                if body[key] == 1 or body[key] == 'True':
                    actiu=True
                else:
                    actiu=False
            elif key == 'superficie':
                superficie=body[key]
            elif key == 'localitat':
                localitat=body[key]
            elif key == 'pais':
                pais=body[key]
        pInteresCercat=puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
        if not pInteresCercat:
            pInteresNou=puntInteres(latitud=latitud, longitud=longitud, idMapa=idMapa, tipus=tipus, actiu=actiu, superficie=superficie, localitat=localitat, pais=pais)
            pInteresNou.save()
            pINou=puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
            serializer = puntInteresSerializer(pINou, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(puntInteresSerializer(pInteresCercat, many=True).data, status=status.HTTP_200_OK)

"""
DELETE /v1/geoInfoSystem/eliminarPuntInteres/?latitud=l&longitud=lo
Aquest mètode elimina el punt d'interes situat en la latitud "l" i longitud "lo". Retorna un 400 BAD REQUEST en cas que no trobi 
cap punt d'interes en les coordenades. Retorna un 404 NOT FOUND en cas que es vulgui eliminar un element que no existeixi.
En altre cas retorna un 200 OK informat que s'ha eliminat correctament el punt d'interes.
"""
@api_view(['DELETE',])
def deletePuntInteres(request):
    if request.method == 'DELETE':
        latitud=request.query_params.get('latitud')
        longitud=request.query_params.get('longitud')
        if not latitud or not longitud:
            return Response('Falten parametres per a poder eliminar la instancia', status=status.HTTP_400_BAD_REQUEST)
        try:
            p=puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
            if not p:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No hi ha cap punt d\'interes amb aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)
        puntInteres.objects.all().filter(latitud=latitud, longitud=longitud).delete()
        return Response('Punt d\'interes eliminat correctament.', status=status.HTTP_200_OK)

###################################################################
# API PER ALS USUARIS.                                            #
###################################################################
"""
GET /v1/geoInfoSystem/getUsuaris/
Aquest mètode retorna tota la informació de tots els usuaris que hi ha en el sistema.
Si no n'hi ha retorna un 404 NOT FOUND, altre cas retorna un 200 OK amb les dades.
"""
@api_view(['GET',])
def getUsuaris(request):
    if request.method == 'GET':
        try:
            usuaris = User.objects.all()
            if not usuaris:
                raise NoContingut
            serializer = UserSerializer(usuaris, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha usuaris.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/getSuperUsuaris/
Aquest mètode retorna tots els superusuaris del sistema.
Retorna un 404 NOT FOUND en cas que no n'hi hagi, en altre cas un 200 OK amb la informació.
"""
@api_view(['GET',])
def getSuperUsuaris(request):
    if request.method=='GET':
        try:
            superusuaris=User.objects.all().filter(is_superuser=True)
            if not superusuaris:
                raise NoContingut
            serializer = UserSerializer(superusuaris, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha superusuaris.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/getUsuarisNormals/
Aquest mètode retorna tots els usuaris del sistema que no son superusuaris.
Retorna un 404 NOT FOUND en cas que no n'hi hagi, en altre cas un 200 OK amb la informació.
"""
@api_view(['GET',])
def getUsuarisNormals(request):
    if request.method == 'GET':
        try:
            usuarisNormals = User.objects.all().filter(is_superuser=False)
            if not usuarisNormals:
                raise NoContingut
            serializer = UserSerializer(usuarisNormals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha usuaris normals.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/getUsuari/<alias>/
Aquest mètode retorna la informació referent a un usuari en especific donat el seu àlies.
En cas que no es passi el àlies retorna un 400 BAD REQUEST. 
En cas que no trobi cap usuari amb aquest àlies retorna un 404 NOT FOUND.
Si el troba retorna un 200 OK amb la informació referent al usuari.
"""
@api_view(['GET',])
def getUsuariEspecific(request, alias):
    if request.method == 'GET':
        if not alias:
            return Response('Falta el alies per a poder cercar el usuari especific.', status=status.HTTP_400_BAD_REQUEST)
        try:
            usuariEspecific=User.objects.all().filter(username=alias)
            if not usuariEspecific:
                raise NoContingut
            serializer = UserSerializer(usuariEspecific, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No existeix aquest usuari', status=status.HTTP_404_NOT_FOUND)

"""
PUT /v1/geoInfoSystem/updateUsuari/?alies=a
Mètode per a actualitzar la informació d'un usuari amb alies "a" (específic). 
En cas que no es trobi cap usuari amb aquest àlies retorna un 404 NOT FOUND. Si no hi ha cap àlies retorna un 400 BAD REQUEST.
En cas que no hi hagi cos en el missatge HTTP PUT retorna un 400 BAD REQUEST, de la mateixa forma que si hi ha algun error en el cos del missatge,
retorna què hi ha malament i un 400 BAD REQUEST.
En altre cas, tot està bé i actualitza l'usuari específic, i per tant retorna un 200 OK i rebota l'usuari.
"""
@api_view(['PUT',])
def updateUsuari(request):
    if request.method == 'PUT':
        if not request.body:
            return Response('Falta passar-li informacio al cos del missatge.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded = request.body.decode('utf-8')
        body=json.loads(body_decoded)
        keys=body.keys()
        errorsInEntryJSON=""
        for key in keys:
            try:
                User._meta.get_field(key)
            except FieldDoesNotExist:
                errorsInEntryJSON=errorsInEntryJSON+'['+key+']'+ 'no es un camp correcte.'
        if errorsInEntryJSON:
            errorsInEntryJSON=errorsInEntryJSON+' Revisa els camps i torna a executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        alies=request.query_params.get('alies')
        if not alies:
            return Response('Falta el alies.', status=status.HTTP_400_BAD_REQUEST)
        try:
            usrEspecific=User.objects.all().filter(username=alies)
            if not usrEspecific:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No hi ha cap usuari amb aquest àlies. S\'aborta la actualització', status=status.HTTP_404_NOT_FOUND)
        aliasChanged = False
        nouAlies =""
        novaContrassenya=""
        hasher=""
        salt=""
        for key in keys:
            if key == 'first_name':
                User.objects.all().filter(username=alies).update(first_name=body[key])
            elif key == 'username':
                aliasChanged=True
                nouAlies=body[key]
                User.objects.all().filter(username=alies).update(username=body[key])
            elif key == 'last_name':
                User.objects.all().filter(username=alies).update(last_name=body[key])
            elif key == 'password':
                novaContrassenya=body[key]
                first_pass = User.objects.all().filter(username=alies)[0].password.split('$')
                hasher = first_pass[0]
                salt = first_pass[1]  # grabbing salt from the first password of the database
                User.objects.all().filter(username=alies).update(password=make_password(novaContrassenya, salt, hasher))
            elif key == 'email':
                regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
                if re.search(regex, body[key]):
                    User.objects.all().filter(username=alies).update(email=body[key])
            elif key == 'superUsuari':
                if body[key] == 'True' or body[key] == 1:
                    superusr=True
                else:
                    superusr=False
                User.objects.all().filter(username=alies).update(is_superuser=superusr)

        #modificacions fetes
        usuariCercat = User.objects.all().filter(username=alies)
        if aliasChanged:
            usuariCercat=User.objects.all().filter(username=nouAlies)

        serializer = UserSerializer(usuariCercat, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


"""
POST /v1/geoInfoSystem/createUsuari/
Mètode que genera un nou usuari. En cas que no hi hagi informació en el cos del missatge HTTP POST retorna un 400 BAD REQUEST.
De la mateixa forma si hi ha algun error en el cos del missatge, informa del problema i retorna un 400 BAD REQUEST.
En altre cas, tot està bé i processa la operació, genera la nova fila en la base de dades i retorna un 201 CREATED i el nou element.
"""
@api_view(['POST',])
def postNewUsuari(request):
    if request.method == 'POST':
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

"""
DELETE /v1/geoInfoSystem/deleteUsuari/<alias>/
Mètode que permet eliminar l'usuari amb el <alias> que ve com a path param a la url. En cas que aquest àlies no hi sigui retorna un 400 BAD REQUEST.
En cas que no trobi cap usuari amb aquest alies retorna un 404 NOT FOUND. En altre cas tot està bé, per tant, retorna un 200 OK i informat que la fila
de la base de dades s'ha eliminat correctament.
"""
@api_view(['DELETE',])
def deleteUsuari(request, alias):
    if request.method=='DELETE':
        if not alias:
            return Response('Falta el alies per a poder eliminar la instancia.', status=status.HTTP_400_BAD_REQUEST)
        try:
            usuariCercat = User.objects.all().filter(username=alias)
            if not usuariCercat:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No hi ha cap usuari amb aquest alies.', status=status.HTTP_404_NOT_FOUND)
        User.objects.all().filter(username=alias).delete()
        return Response('Usuari eliminat correctament.', status=status.HTTP_200_OK)

###################################################################
# API PER ALS LOCALS                                              #
###################################################################
"""
GET /v1/geoInfoSystem/getLocals/
Mètode que permet recuperar tota la informació referent als locals que hi ha presents en la base de dades.
En cas que no en trobi retornara un 404 NOT FOUND, en altre cas, retorna un 200 OK amb la informació demanada.
"""
@api_view(['GET',])
def getLocals(request):
    if request.method == 'GET':
        try:
            locals = local.objects.all()
            if not locals:
                raise NoContingut
            serializer = localSerializer(locals, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha locals.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/getLocalByLatLong/<latitud>/<longitud>/
Mètode que retorna la informació referent al local situat en la latitud=<latitud> i la longitud=<longitud>. Aquestes vénen com a path param.
En cas que no hi hagi un dels dos o cap, retorna un 400 BAD REQUEST. En cas que no trobi aquest punt d'interes, retorna un 404 BAD REQUEST. 
En altre cas, retorna un 200 OK amb la informació demanada.
"""
@api_view(['GET',])
def getLocalEspecificByLatLong(request, latitud, longitud):
    if request.method == 'GET':
        if not latitud or not longitud:
            return Response('Falten els parametres per a poder executar la operacio.', status=status.HTTP_400_BAD_REQUEST)
        try:
            punt1=puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
            if not punt1:
                raise NoContingut
            localCercat = local.objects.all().filter(localitzacio=punt1)
            if not localCercat:
                raise NoContingut
            return Response(localSerializer(localCercat, many=True).data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha cap local en aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)

"""
GET /v1/geoInfoSystem/getLocalByName/<nomLocal>/
Mètode que retorna el local amb el nom=nomLocal (path param).
En cas que aquest paràmetre no existeixi retorna un 400 BAD REQUEST. En altre cas, si no hi ha cap local amb el mateix nom, retorna un 404 NOT FOUND.
En altre cas retorna un 200 OK amb la informació referent a la que s'ha demanat.
"""
@api_view(['GET',])
def getLocalEspecificByName(request, nomLocal):
    if request.method == 'GET':
        if not nomLocal:
            return Response('Falta el parametre per a poder executar la operacio.', status=status.HTTP_400_BAD_REQUEST)
        try:
            localCercat=local.objects.all().filter(nomLocal=nomLocal)
            if not localCercat:
                raise NoContingut
            return Response(localSerializer(localCercat, many=True).data, status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha cap local amb aquest nom.', status=status.HTTP_404_NOT_FOUND)

"""
PUT /v1/geoInfoSystem/updateLocalByLatLong/<nomLocal>/<latitud>/<longitud>/
Mètode que permet actualitzar la informació del local situat en la latitud=<latitud> i longitud=<longitud>. Ambdós són path param.
En cas que no existeixi algun dels dos o cap, retorna un 400 BAD REQUEST. Juntament en què no hi hagi el cos del missatge HTTP PUT.
En cas que hi hagi algun problema en el cos del missatge, també retornarà un 400 BAD REQUEST i informarà sobre els problemes presents en el cos.
En altre cas, tot va bé i per tant actualitzarà els camps i retornarà un 200 OK i el local actualitzat.

La idea d'aquest PUT és que també permet la modificacio de la latitud i la longitud del local si aquestes coordenades conformen un punt d'interes emmagatzemat prèviament.
"""
@api_view(['PUT',])
def updateLocalByLatLong(request, nomLocal, latitud, longitud):
    if request.method == 'PUT':
        if not latitud or not longitud or not nomLocal:
            return Response('Falten els parametres per a executar la operacio d\'actualització del local.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded = request.body.decode('utf-8')
        body = json.loads(body_decoded)
        keys = body.keys()
        errorsInEntryJSON = ""
        for key in keys:
            try:
                if key != 'latitud' and key != 'longitud':
                    local._meta.get_field(key)
            except FieldDoesNotExist:
                errorsInEntryJSON = errorsInEntryJSON + '[' + str(key) + "] no es un camp correcte."
        if errorsInEntryJSON:
            errorsInEntryJSON = errorsInEntryJSON + 'Revisa els camps i torna executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        try:
            puntInteresCercat = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
            if not puntInteresCercat:
                raise NoContingut
            localCercat=local.objects.all().filter(localitzacio=puntInteresCercat, nomLocal=nomLocal)
            if not localCercat:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No hi ha cap local en aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)
        # No hi ha error en les dades dentrada
        puntInteresCercat = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
        novaLatitud=0.0
        novaLongitud=0.0
        for key in keys:
            if key == 'nomLocal':
                local.objects.all().filter(localitzacio=puntInteresCercat).update(nomLocal=body[key])
            elif key == 'puntuacio':
                local.objects.all().filter(localitzacio=puntInteresCercat).update(puntuacio=body[key])
            elif key == 'categoria':
                local.objects.all().filter(localitzacio=puntInteresCercat).update(categoria=body[key])
            elif key == 'anyConstruccio':
                local.objects.all().filter(localitzacio=puntInteresCercat).update(anyConstruccio=body[key])
            elif key == 'descripcio':
                local.objects.all().filter(localitzacio=puntInteresCercat).update(descripcio=body[key])
            elif key == 'latitud':
                novaLatitud=body[key]
            elif key == 'longitud':
                novaLongitud=body[key]

        if novaLatitud != 0.0 and novaLongitud != 0.0:
            try:
                pInteresNou = puntInteres.objects.all().filter(latitud=novaLatitud, longitud=novaLongitud)[0]
                if not pInteresNou:
                    raise NoContingut
                local.objects.all().filter(localitzacio=puntInteresCercat).update(localitzacio=pInteresNou)
                localNou = local.objects.all().filter(localitzacio=pInteresNou)
                return Response(localSerializer(localNou, many=True).data, status=status.HTTP_200_OK)
            except Exception or NoContingut:
                return Response('Actualizat correctament els camps passats, pero la localitzacio es la mateixa perque no hi ha cap punt interes amb aquestes caracteristiques.', status=status.HTTP_200_OK)
        else:
            #en altre cas, hi ha la mateixa latitud i longitud, per tant no canvia en punt de interes.
            localSearched = local.objects.all().filter(localitzacio=puntInteresCercat)
            return Response(localSerializer(localSearched, many=True).data, status=status.HTTP_200_OK)

"""
PUT /v1/geoInfoSystem/updateLocalByName/<nomLocal>/
Mètode que permet la actualizació d'un local però ara amb el nom del local = <nomLocal> com a path param.
En cas que no hi hagi cap path param retornarà un 400 BAD REQUEST, de la mateixa forma que no hi hagi cap cos de missatge. 
En cas que no trobi cap local amb aquest nom retornarà un 404 NOT FOUND.
En altre cas retornarà un 200 OK amb la informació del local actualitzada.
"""
@api_view(['PUT',])
def updateLocalByName(request, nomLocal):           #No provat. sha de provar
    if request.method == 'PUT':
        if not nomLocal:
            return Response('Falta el nom del local, s\'aborta la operacio d\'actualització', status=status.HTTP_400_BAD_REQUEST)
        if not request.body:
            return Response('Cal passar informacio al cos del missatge.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded = request.body.decode('utf-8')
        body = json.loads(body_decoded)
        keys = body.keys()
        errorsInEntryJSON = ""
        for key in keys:
            try:
                local._meta.get_field(key)
            except FieldDoesNotExist:
                errorsInEntryJSON = errorsInEntryJSON + '[' + str(key) + "] no es un camp correcte."
        if errorsInEntryJSON:
            errorsInEntryJSON = errorsInEntryJSON + 'Revisa els camps i torna executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        try:
            localCercat = local.objects.all().filter(nomLocal=nomLocal)
            if not localCercat:
                raise NoContingut
        except Exception or NoContingut:
            return Response('No s\'ha trobat cap local anomenat '+str(nomLocal), status=status.HTTP_404_NOT_FOUND)
        # No hi ha error en les dades dentrada
        nouNomLocal=""
        for key in keys:
            if key == 'nomLocal':
                nouNomLocal=body[key]
            elif key == 'puntuacio':
                local.objects.all().filter(nomLocal=nomLocal).update(puntuacio=body[key])
            elif key == 'categoria':
                local.objects.all().filter(nomLocal=nomLocal).update(categoria=body[key])
            elif key == 'anyConstruccio':
                local.objects.all().filter(nomLocal=nomLocal).update(anyConstruccio=body[key])
            elif key == 'descripcio':
                local.objects.all().filter(nomLocal=nomLocal).update(descripcio=body[key])

        localSeached = local.objects.all().filter(nomLocal=nomLocal)
        if nouNomLocal:
            local.objects.all().filter(nomLocal=nomLocal).update(nomLocal=nouNomLocal)
            localSeached = local.objects.all().filter(nomLocal=nouNomLocal)
            return Response(localSerializer(localSeached, many=True).data, status=status.HTTP_200_OK)
        else:
            return Response(localSerializer(localSeached, many=True).data, status=status.HTTP_200_OK)

"""
POST /v1/geoInfoSystem/createLocal/
Mètode dedicat a la creació d'un nou local. 
En cas que no hi hagi cap cos de missatge en el HTTP POST retornarà un 400 BAD REQUEST, de la mateixa forma en que no hi hagi en el 
cos del missatge la latitud i la longitud referents al punt d'interès al qual està lligat el local.
En cas que no es trobi un local en la latitud i longitud donada, retornara un 404 NOT FOUND i no es procedirà a la creació.
En cas que tot estigui bé, es crearà la nova fila a la base de dades i retornarà un 201 CREATED amb el nou local.
"""
@api_view(['POST',])
def postNewLocal(request):
    if request.method == 'POST':
        if not request.body:
            return Response('Falta afegir dades en el cos del missatge.', status=status.HTTP_400_BAD_REQUEST)
        body_decoded = request.body.decode('utf-8')
        body = json.loads(body_decoded)
        keys = body.keys()
        if 'latitud' and 'longitud' not in keys:
            return Response('Per a crear la la nova instancia cal afegir la latitud i la longitud.', status=status.HTTP_400_BAD_REQUEST)
        errorsInEntryJSON = ""
        for key in keys:
            try:
                if key != 'latitud' and key != 'longitud':
                    local._meta.get_field(key)
            except FieldDoesNotExist:
                    errorsInEntryJSON = errorsInEntryJSON + '[' + str(key) + "] no es un camp correcte."
        if errorsInEntryJSON:
            errorsInEntryJSON = errorsInEntryJSON + 'Revisa els camps i torna executar!'
            return Response(errorsInEntryJSON, status=status.HTTP_400_BAD_REQUEST)
        try:
            puntInteresCercat=puntInteres.objects.all().filter(latitud=body['latitud'], longitud=body['longitud'])
            if not puntInteresCercat:
                raise NoContingut
        except:
            return Response('No hi ha cap punt interes amb aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)
        # no hi ha errors en el cos del missatge
        nomLocal=""
        puntuacio=0
        categoria=""
        anyConstruccio=0
        descripcio=""
        latitud=0.0
        longitud=0.0
        for key in keys:
            if key == 'nomLocal':
                nomLocal=body[key]
            elif key == 'puntuacio':
                puntuacio=body[key]
            elif key == 'categoria':
                categoria=body[key]
            elif key == 'anyConstruccio':
                anyConstruccio=body[key]
            elif key == 'descripcio':
                descripcio=body[key]
            elif key == 'latitud':
                latitud=body[key]
            elif key == 'longitud':
                longitud=body[key]

        punt_to_assign = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
        newLocal = local(localitzacio=punt_to_assign, nomLocal=nomLocal,puntuacio=puntuacio,categoria=categoria,anyConstruccio=anyConstruccio,descripcio=descripcio)
        newLocal.save()
        localSeached = local.objects.all().filter(localitzacio=punt_to_assign)
        return Response(localSerializer(localSeached, many=True).data, status=status.HTTP_201_CREATED)

"""
DELETE /v1/geoInfoSystem/deleteLocalByLatLong/?latitud=l&longitud=lo&local=nom
Mètode que permet eliminar el local situat en la latitud=l, la longitud=lo i local=nom. En cas que no hi siguin aquests query param
es retornarà un 400 BAD REQUEST.
En cas que no es trobi cap local en aquestes coordenades, es retornarà un 404 NOT FOUND. En altre cas s'eliminarà el local i es retornarà un 200 OK
i un missatge informant de la eliminació.
"""
@api_view(['DELETE',])
def deleteLocalByLatLong(request):
    if request.method == 'DELETE':
        latitud = request.query_params.get('latitud')
        longitud = request.query_params.get('longitud')
        nomLocal = request.query_params.get('local')
        nomLocal=urllib.parse.unquote(nomLocal)
        if not latitud or not longitud or not nomLocal:
            return Response('Falta la latitud i/o la longitud per a eliminar el local. S\'aborta la operacio.', status=status.HTTP_400_BAD_REQUEST)
        try:
            p=puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
            if not p:
                raise NoContingut
            local.objects.all().filter(localitzacio=p, nomLocal=nomLocal).delete()
            return Response('Local eliminat correctament.', status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha cap punt d\'interes en aquestes coordenades.', status=status.HTTP_404_NOT_FOUND)

"""
DELETE /v1/geoInfoSystem/deleteLocalByNom/?local=nomLocal
Mètode que permet eliminar el local donat el nom per query param (local). 
En cas que no hi hagi el nom del local retornarà un 400 BAD REQUEST. En cas que no trobi cap local amb el nom donat 
retornarà un 404 NOT FOUND. En altre cas retornarà un 200 OK i informant que s'ha eliminat el local correctament.
"""
@api_view(['DELETE',])
def deleteLocalByName(request):
    if request.method == 'DELETE':
        nomLocal=request.query_params.get('local')
        nomLocal = urllib.parse.unquote(nomLocal)
        if not nomLocal:
            return Response('Falta el nom del local', status=status.HTTP_400_BAD_REQUEST)
        try:
            l=local.objects.all().filter(nomLocal=nomLocal)
            if not l:
                raise NoContingut
            local.objects.all().filter(nomLocal=nomLocal).delete()
            return Response('Local eliminat correctament.', status=status.HTTP_200_OK)
        except Exception or NoContingut:
            return Response('No hi ha cap punt d\'interes amb aquest nom.', status=status.HTTP_404_NOT_FOUND)


################################################################
# Secció per a cridar la vista d'entrada/registre/login/logout #
################################################################

""" 
Mètode que permet visualitzar la pàgina d'inici
"""
def home(response):
    return render(response, "home/home.html",{})

"""
Mètode que mostra la pàgina per a registrar un nou usuari
"""
def paginaRegistrarse(request):
    if request.method == 'POST':
        password1=request.POST['password1']
        nou_usuari = User()
        nou_usuari.username=request.POST['username']
        if request.POST['first_name']:
            nou_usuari.first_name=request.POST['first_name']
        if request.POST['last_name']:
            nou_usuari.last_name = request.POST['last_name']
        nou_usuari.email=request.POST['email']
        nou_usuari.set_password(password1)
        print(nou_usuari)
        nou_usuari.save()
        return redirect("/")
    return render(request, "usuaris/registrar1.html", {})

def check_values_register_data(request):
    username = urllib.parse.unquote(request.GET['username'])
    password1 = urllib.parse.unquote(request.GET['password1'])
    password2 = urllib.parse.unquote(request.GET['password2'])
    email = urllib.parse.unquote(request.GET['email'])
    data = {}
    data['tot_ok']="true"
    if User.objects.all().filter(username=username):
        data['tot_ok']="false"
    if len(password1) < 8:
        data['tot_ok'] = "false"
    if password1 != password2:
        data['tot_ok']="false"
    if email:
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex, email):
            data['tot_ok'] = "false"
    res_json = json.dumps(data)
    return HttpResponse(res_json, content_type='json')

def check_empty_register_data(request):
    if request.method == 'GET':
        username=urllib.parse.unquote(request.GET['username'])
        first_name=urllib.parse.unquote(request.GET['first_name'])
        last_name=urllib.parse.unquote(request.GET['last_name'])
        password1=urllib.parse.unquote(request.GET['password1'])
        password2=urllib.parse.unquote(request.GET['password2'])
        email=urllib.parse.unquote(request.GET['email'])
        data={}
        if username == "" or first_name == "" or last_name == "" or password1 == "" or password2 == "" or email == "":
            data['buit'] = "true"
        else:
            data['buit'] = "false"
        res_json = json.dumps(data)
        return HttpResponse(res_json, content_type="json")


#############################################################################
# MÈTODES REFERENTS A LA VISTA ON TREBALLAREM AMB EL MAPA                   #
#############################################################################
def mostrarMapa(response):
    puntsInteresCercats = puntInteres.objects.all()
    localsimp = local.objects.all()

    claus_foranes_categories_local = local.objects.all().values_list('categoria', flat=True)
    categoriesCercades = categoriaLocal.objects.all().filter(pk__in = claus_foranes_categories_local)

    claus_foranes_localitzacio_puntInteres = puntInteres.objects.all().values_list('localitat', flat=True)
    localitzacionsC = localitzacio.objects.all().filter(pk__in=claus_foranes_localitzacio_puntInteres)

    locals = serializers.serialize("json", localsimp)
    punts = serializers.serialize("json", puntsInteresCercats)
    categories = serializers.serialize("json", categoriesCercades)
    localitzacions = serializers.serialize("json", localitzacionsC)

    provincies = localitzacio.objects.all().values_list('provincia', flat=True).distinct()
    dict={}
    i=1
    for res in provincies:
       dict['prov'+str(i)] = res
       i = i + 1
    provincies = json.dumps(dict)
    print(provincies)
    poblesTgn = localitzacio.objects.all().filter(provincia = 'Tarragona').values_list('ciutat', 'comarca')
    dict = {}
    i=1
    for res in poblesTgn:
        dict['poble'+str(i)] = res[0]+" ("+res[1]+"), "+"Tarragona"
        i= i + 1
    poblesDeTgn = json.dumps(dict)
    tipus = categoriaLocal.objects.all()
    categoriesT = serializers.serialize('json', tipus)

    rand_id_puntInteres = random.choice(list(puntInteres.objects.all().values_list('id',flat=True)))

    pIntRand_latitud = str(puntInteres.objects.all().filter(id=rand_id_puntInteres)[0].latitud)
    pIntRand_longitud = str(puntInteres.objects.all().filter(id=rand_id_puntInteres)[0].longitud)
    nom_local_rand = local.objects.all().filter(localitzacio=rand_id_puntInteres)[0].nomLocal

    #LIMITACIO DE NO PAGAR API: NO PUC FER CERQUES.... (searchbox item de google)
    return render(response, "puntsGeografics/map.html", {'latitudRand': pIntRand_latitud, 'longitudRand': pIntRand_longitud, 'nomLocalRand':nom_local_rand,'totesCategories':categoriesT,'poblesTGN':poblesDeTgn, 'provincies':provincies,'puntsInteres': punts, 'locals': locals, 'categoriesMapa': categories, 'localitzacionsMapa':localitzacions})

def estadistiques_inicials(request):
    resultatsInicials = {}
    res = {}
    categoriaInicial = categoriaLocal.objects.all().filter(categoria='Restauració')[0]
    pobleInicial = localitzacio.objects.all().filter(ciutat='Aiguamúrcia')[0]
    actiu = False
    # RESULTAT AMB ELS FILTRES ESTABLERTS
    punt_filtre1 = puntInteres.objects.all().filter(localitat=pobleInicial, actiu=actiu)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria=categoriaInicial)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in = punt_filtre1, categoria=categoriaInicial).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in = fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['FiltresAplicats'] = res_filtre1
    res['numResultats'] = str(len(llocs_filtre1))
    res['puntinteresFiltresAplicats'] = res_lat_lng
    resultatsInicials['FitresEstablerts'] = res

    res = {}
    # RESULTAT ON SURTEN TOTS ELS PUNTS/LOCALS DEL MATEIX POBLE (TANT ACTIUS COM NO ACTIUS)
    punt_filtre1 = puntInteres.objects.all().filter(localitat=pobleInicial)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['puntsPoble'] = res_filtre1
    res['numMateixPoble'] = str(len(llocs_filtre1))
    res['puntsInterespuntsMateixPoble'] = res_lat_lng
    resultatsInicials['FiltreMateixPoble'] = res

    res = {}
    # RESULTAT NEGANT EL ACTIU MATEIXA CATEGORIA
    punt_filtre1 = puntInteres.objects.all().filter(localitat=pobleInicial, actiu=not actiu)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria=categoriaInicial)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria=categoriaInicial).values_list('localitzacio_id',flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['resNegatActiuMateixaCat'] = res_filtre1
    res['numResNegatActiuMateixaCat'] = str(len(llocs_filtre1))
    res['resPuntInteresNegatActiuMateixaCat'] = res_lat_lng
    resultatsInicials['FiltreNegatActiuMateixaCat'] = res

    res = {}
    # RESULTAT MATEIX POBLE, ACTIU QUE VE I NO MATEIXA CATEGORIA
    punt_filtre1 = puntInteres.objects.all().filter(localitat=pobleInicial, actiu=actiu)
    altresCategories_filtre1 = categoriaLocal.objects.all().exclude(categoria=categoriaInicial)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria__in=altresCategories_filtre1)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria__in=altresCategories_filtre1).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['resMateixPobleNoMateixaCat'] = res_filtre1
    res['numresMateixPobleNoMateixaCat'] = str(len(llocs_filtre1))
    res['resPuntInteresMateixPobleNoMateixaCat'] = res_lat_lng
    resultatsInicials['FiltreMateixPobleNoMateixaCat'] = res

    res = {}
    # RESTULTAT NO MATEIX POBLE, ACTIU QUE VE I MATEIXA CATEGORIA
    punt_filtre1 = puntInteres.objects.all().exclude(localitat=pobleInicial).filter(actiu=actiu)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria=categoriaInicial)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1,categoria=categoriaInicial).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['resNoMateixPobleMateixaCat'] = res_filtre1
    res['numResNoMateixPobleMateixaCat'] = str(len(llocs_filtre1))
    res['resPuntInteresNoMateixPobleMateixaCat'] = res_lat_lng
    resultatsInicials['FiltreNoMateixPobleMateixaCat'] = res

    res = {}
    # RESULTAT NO MATEIX POBLE, ACTIU NEGAT I NO MATEIXA CATEGORIA
    punt_filtre1 = puntInteres.objects.all().exclude(localitat=pobleInicial).filter(actiu=not actiu)
    altresCategories_filtre1 = categoriaLocal.objects.all().exclude(categoria=categoriaInicial)
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1, categoria__in=altresCategories_filtre1)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1,categoria__in=altresCategories_filtre1).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['resNoMateixPobleNoMateixaCategoria'] = res_filtre1
    res['numResNoMateixPobleNoMateixaCategoria'] = str(len(llocs_filtre1))
    res['resPuntInteresNoMateixPobleNoMateixaCategoria'] = res_lat_lng
    resultatsInicials['FiltreNoMateixPobleNoMateixaCat'] = res

    res = {}
    # RESULTAT AMB TOTES LES DADES DE LA DB
    punt_filtre1 = puntInteres.objects.all()
    llocs_filtre1 = local.objects.all().filter(localitzacio__in=punt_filtre1)
    fk_id_puntInteres = local.objects.all().filter(localitzacio__in=punt_filtre1).values_list('localitzacio_id', flat=True)
    puntsInteresLatLng = puntInteres.objects.all().filter(id__in=fk_id_puntInteres)
    res_lat_lng = serializers.serialize('json', puntsInteresLatLng)
    res_filtre1 = serializers.serialize('json', llocs_filtre1)
    res['infoDB'] = res_filtre1
    res['numinfoDB'] = str(len(llocs_filtre1))
    res['puntsIntresinfoDB'] = res_lat_lng
    resultatsInicials['FiltreTotaDB'] = res

    initial_statistics_data = json.dumps(resultatsInicials)
    return HttpResponse(initial_statistics_data, content_type='json')

def mostrarPuntEspecific(response, nomLocal,latitud, longitud):
    nomLocal = urllib.parse.unquote(nomLocal)
    try:
        punt = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
        if not punt:
            raise NoContingut
        loc = local.objects.all().filter(nomLocal=nomLocal, localitzacio=punt)
        if not loc:
            raise NoContingut
    except Exception or NoContingut:
        return render(response, "errors/ErrorFile.html",{})
    puntInteresC = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)
    p = puntInteresC[0]
    localitat  = p.localitat
    print(localitat)
    localEspecific = local.objects.all().filter(nomLocal=nomLocal)
    categoria = localEspecific[0].categoria
    print(categoria)
    altresPuntsInteres = puntInteres.objects.all().filter(localitat=p.localitat).exclude(latitud=latitud, longitud=longitud)
    punts=[]
    for punt in altresPuntsInteres:
        punts+=[punt]
    locals = local.objects.all().exclude(nomLocal=nomLocal)
    altresLocals=[]
    for punt in punts:
        for l in locals:
            if l.localitzacio.localitat == punt.localitat:
                altresLocals+=[l]
    print(punts)
    print(altresLocals)
    punt = serializers.serialize("json", puntInteresC)
    localE = serializers.serialize("json", localEspecific)
    altresLocals = serializers.serialize("json", altresLocals)
    punts = serializers.serialize("json", punts)
    if altresLocals != "[]" and punts!= "[]":
        return render(response, "puntsGeografics/informacioDetallada.html", {'categoria':categoria,'localitat':localitat,'puntInteres':punt, 'local': localE, 'altresLocals' : altresLocals, 'altresPuntsInteres': punts, 'altres': True})
    else:
        return render(response, "puntsGeografics/informacioDetallada.html", {'categoria':categoria,'localitat':localitat, 'puntInteres': punt, 'local': localE, 'altresLocals': altresLocals, 'altresPuntsInteres': punts, 'altres': False})

def loginPage(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect("/")
        else:
            user = User.objects.all().filter(username=username)
            user=user[0]
            if user.check_password(password):
                if user.is_active:
                    login(request,user)
                    return redirect("/")
    return render(request, 'usuaris/login.html',{})


def checkInputsLogIn(request):
    if request.method == 'GET':
        data={}
        username = urllib.parse.unquote(request.GET['nomUsuari'])
        password = urllib.parse.unquote(request.GET['contrassenyaUsuari'])
        if username == "" or password == "":
            data['buit'] = "true"
        if username == "" and password == "":
            data['buit'] = "true"
        if username != "" and password != "":
            data['buit'] = "false"
        res_json = json.dumps(data)
        return HttpResponse(res_json, content_type="json")

def checkUserToLogIn(request):
    if request.method == 'GET':
        data={}
        username = urllib.parse.unquote(request.GET['nomUsuari'])
        passwd = urllib.parse.unquote(request.GET['contrassenyaUsuari'])
        userMaster = authenticate(username=username, password=passwd)
        if userMaster is not None:
            if userMaster.is_active:
                data['tot_ok'] = "true"
            else:
                data['tot_ok'] = "false"
        else:
            userMaster= User.objects.all().filter(username=username)
            if not userMaster:
                data['tot_ok'] = "false"
            else:
                user = userMaster[0]
                if user.check_password(passwd):
                    if user.is_active:
                        data['tot_ok'] = "true"
                    else:
                        data['tot_ok'] = "false"
                else:
                    data['tot_ok'] = "false"
        res_json = json.dumps(data)
        return HttpResponse(res_json, content_type='json')





def logout(request):
    do_logout(request)
    return redirect("/")


@login_required(login_url='/v1/geoInfoSystem/inicia_sessio/')
def profilePage(request):
    return render(request, "usuaris/profilePage.html", {})


@login_required(login_url='/v1/geoInfoSystem/inicia_sessio/')
def updateUsuari(request, codi):
    errors = []
    if request.method == 'POST':
        user_name=request.user
        err_mail=False
        err_Nom = False
        err_cognom = False
        err_passwd = False
        if codi == 'actualitzaMail':
            mail1 = request.POST['email']
            mail2 = request.POST['email1']
            if mail1 != mail2:
                err_mail = True
                errors+=['Els dos correus no coincideixen, siusplau, torna a intentar-ho.']
            else:
                User.objects.all().filter(username=user_name).update(email = mail1)
        elif codi == 'actualitzaNom':
            nom1 = request.POST['first_name']
            nom2 = request.POST['first_name1']
            if nom1 != nom2:
                err_Nom = True
                errors+=['Els dos noms no coincideixen, siusplau, torna a intentar-ho.']
            else:
                if nom1 == user_name:
                    err_Nom = True
                    errors+=['El nom no pot coincidir amb el nom d\'usuari.']
                else:
                    User.objects.all().filter(username=user_name).update(first_name=nom1)
        elif codi== 'actualitzaCognom':
            cognom1 = request.POST['last_name']
            cognom2 = request.POST['last_name1']
            if cognom1 != cognom2:
                err_cognom = True
                errors+=['Els cognoms no coincideixen, siusplau, torna a intentar-ho.']
            else:
                User.objects.all().filter(username=user_name).update(last_name=cognom1)

        elif codi == 'actualitzaContrassenya':
            password1=request.POST['password']
            password2=request.POST['password1']
            if password1 != password2:
                err_passwd = True
                errors+=['Les contrassenyes no coincideixen, siusplau, torna a intentar-ho.']
            else:
                first_pass = User.objects.all().filter(username=user_name)[0].password.split('$')
                hasher = first_pass[0]
                salt = first_pass[1]  # grabbing salt from the first password of the database
                User.objects.all().filter(username=user_name).update(password=make_password(password1, salt, hasher))
        if not errors:
            return redirect("/v1/geoInfoSystem/el_meu_espai/")
        else:
            return render(request, "usuaris/updateUsuari.html", {'chMail': err_mail, 'chNom': err_Nom, 'chCog': err_cognom, 'chPass': err_passwd, 'errors': errors})
    else:
        codi = urllib.parse.unquote(codi)
        codiTallat = codi.split()
        chMail = False
        if codiTallat[0].isupper():
            chMail = True
        chNom = False
        if codiTallat[1].isupper():
            chNom=True
        chCog = False
        if codiTallat[2].isupper():
            chCog = True
        chPass = False
        if codiTallat[3].isupper():
            chPass = True
        return render(request, "usuaris/updateUsuari.html",{'chMail':chMail, 'chNom':chNom, 'chCog':chCog, 'chPass':chPass, 'errors': errors})

def baixa(request):
    curr_usr = request.user
    User.objects.all().filter(username=curr_usr).delete()
    return redirect("/")

def unauthorizedpage(response):
    return render(response, "errors/NoAutoritzat.html", {})


def ciutatsPerProvincia(request):
    if request.method == 'GET':
        provincia = request.GET['provincia']
        localitzacions = localitzacio.objects.all().filter(provincia=provincia).values_list('ciutat', 'comarca')
        dict={}
        res={}
        i=1
        for elem in localitzacions:
            dict['localitzacio'+str(i)] = elem[0]+" ("+elem[1]+")"
            i = i +1
        res['data'] = dict
        loc = json.dumps(res)
        return HttpResponse(loc, content_type='json')

def res_ajax_estadistiques(request):
    if request.method == 'GET':
        ciutat = urllib.parse.unquote(request.GET['poblacio'])
        actiu = urllib.parse.unquote(request.GET['actiu'])
        categoria = urllib.parse.unquote(request.GET['categoria'])
        bActiu = False
        cAux = ciutat.split(' (')[0]
        if actiu =='True':
            bActiu = True

        poble = localitzacio.objects.all().filter(ciutat = cAux)[0] #nom del poble
        categoriaC = categoriaLocal.objects.all().filter(categoria=categoria)[0] #categoria
        res = {}
        dict = {}
        # RESULTAT AMB ELS FILTRES ESTABLERTS
        punt = puntInteres.objects.all().filter(localitat = poble, actiu = bActiu)
        lloc = local.objects.all().filter(localitzacio__in = punt, categoria = categoriaC)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in = punt, categoria = categoriaC).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in = fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['resFiltres'] = data
        dict['descripcio'] = 'Resultat obtingut desprès d\'aplicar tots els filtres.'
        dict['numlocalsTotsFiltres'] = str(len(lloc))
        dict['puntIntersFiltresActuals'] = res_json_lat_lng
        res['AllFilters'] = dict


        dict = {}
        # RESULTAT ON SURTEN TOTS ELS PUNTS/LOCALS DEL MATEIX POBLE (TANT ACTIUS COM NO ACTIUS)
        punt = puntInteres.objects.all().filter(localitat=poble)
        lloc = local.objects.all().filter(localitzacio__in=punt)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['llocMateixPoble'] = data
        dict['descripcio'] = 'Tots els locals que es troben en la mateixa ciutat (tant actius com no actius).'
        dict['numLocalsMateixPoble'] = str(len(lloc))
        dict['puntsIntersMateixPoble'] = res_json_lat_lng
        res['FilterMateixPoble'] = dict

        dict = {}
        # RESULTAT NEGANT EL ACTIU MATEIXA CATEGORIA
        punt = puntInteres.objects.all().filter(localitat=poble, actiu=not bActiu)
        lloc = local.objects.all().filter(localitzacio__in=punt, categoria=categoriaC)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt, categoria=categoriaC).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['llocFilterNegat'] = data
        dict['descripcio'] = 'Resultats obtinguts deprès d\'haver negat si és actiu i mantenint la mateixa categoria.'
        dict['numLocalsNegantActiuMateixaCategoria'] = str(len(lloc))
        dict['puntInteresNegatActiuMateixaCategoria'] = res_json_lat_lng
        res['FilterNegantActiu'] = dict


        dict = {}
        # RESULTAT MATEIX POBLE, ACTIU QUE VE I NO MATEIXA CATEGORIA
        punt = puntInteres.objects.all().filter(localitat=poble, actiu=bActiu)
        altresCategories = categoriaLocal.objects.all().exclude(categoria=categoria)
        lloc = local.objects.all().filter(localitzacio__in=punt, categoria__in=altresCategories)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt, categoria__in=altresCategories).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['filtreEstrany'] = data
        dict['descripcio'] = 'Resultat obtingut de aplicar el mateix poble amb l\'actiu que s\'ha donat i una categoria diferent a la donada.'
        dict['numResMateixPobleNotMateixaCategoria'] = str(len(lloc))
        dict['puntsInteresfiltreExtrany'] =res_json_lat_lng
        res['FiltreResMateixPobleNotCategoriaDonada'] = dict

        dict = {}
        # RESTULTAT NO MATEIX POBLE, ACTIU QUE VE I MATEIXA CATEGORIA
        punt = puntInteres.objects.all().exclude(localitat=poble).filter(actiu=bActiu)
        lloc = local.objects.all().filter(localitzacio__in=punt, categoria=categoriaC)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt, categoria=categoriaC).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['filtreEstrany']=data
        dict['descripcio'] = 'Resultat de aplicar altres pobles i actiu que s\'ha donat i la mateixa categoria donada.'
        dict['numResNoMateixPobleMateixaCategoria'] = str(len(lloc))
        dict['puntsInteresfiltreExtrany'] = res_json_lat_lng
        res['FiltreResNoMateixPobleMateixaCategoria'] = dict

        dict = {}
        # RESULTAT NO MATEIX POBLE, ACTIU NEGAT I NO MATEIXA CATEGORIA
        punt = puntInteres.objects.all().exclude(localitat=poble).filter(actiu=not bActiu)
        llCategories = categoriaLocal.objects.all().exclude(categoria=categoriaC)
        lloc = local.objects.all().filter(localitzacio__in=punt, categoria__in=llCategories)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt, categoria__in=llCategories).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['filtreEstrany'] = data
        dict['descripcio'] = 'Resultat de aplicar un poble diferent al donat, actiu negat i no mateixa categoria.'
        dict['numResNoMateixPobleNoMateixaCategoria'] = str(len(lloc))
        dict['PuntInteresfiltreExtrany'] = res_json_lat_lng
        res['FiltreResNoMateixPobleNoMateixaCategoria'] = dict

        dict = {}
        # RESULTAT AMB TOTES LES DADES DE LA DB
        punt = puntInteres.objects.all()
        lloc = local.objects.all().filter(localitzacio__in=punt)
        fk_id_puntsInteres = local.objects.all().filter(localitzacio__in=punt).values_list('localitzacio_id', flat=True)
        res_lat_lng = puntInteres.objects.all().filter(id__in=fk_id_puntsInteres)
        res_json_lat_lng = serializers.serialize('json', res_lat_lng)
        data = serializers.serialize('json', lloc)
        dict['llocsDB'] = data
        dict['descripcio'] = 'Totes les dades.'
        dict['numElemsReals'] = str(len(lloc))
        dict['puntsInteresLlocsDB'] = res_json_lat_lng

        res['RealsDB'] = dict
        res_json = json.dumps(res)
        return HttpResponse(res_json, content_type='json')

@user_passes_test(lambda u: u.is_superuser)
def crearNouPuntInteres(request):       #Només pots entrar si és administrador de la pàgina
    provincies = localitzacio.objects.all().values_list('provincia', flat=True).distinct()
    i=1
    provinciesMostrarAux={}
    for prov in provincies:
        provinciesMostrarAux['prov'+str(i)] = prov
        i = i + 1
    provinciesMostrar=json.dumps(provinciesMostrarAux)
    categories = categoriaLocal.objects.all()
    categoriesMostrar = serializers.serialize("json", categories)
    poblacions = localitzacio.objects.all().filter(provincia='Tarragona')
    poblacionsMostrar = serializers.serialize("json", poblacions)
    if request.method == 'POST':
        errors = []
        # em ve nomPunt,lat<espai>lng
        altresPuntsPerProcessar = json.loads(request.POST['altresPunts'])
        puntNou = request.POST['puntPerProcessar1']
        nomLocal = request.POST['nomLocal']
        descripcioLocal = request.POST['descripcioLocal']
        tipus = request.POST['tipus']
        llocActiu = request.POST['llocActiu']
        superficie = request.POST['superficie']
        localitat = request.POST['poblacio'] #em ve: poblacio<espai>(comarca),<espai>provincia
        puntuacio = request.POST['p']
        any = request.POST['any']
        midaLlistaString = request.POST['midaLlista']

        if not nomLocal:
            errors+=['Cal posar un nom al punt d\'intereres.']
        if not descripcioLocal:
            errors+=['Cal afegir una descripció.']
        if not tipus:
            errors+=['Cal afegir un tipus.']
        if not superficie:
            errors+=['Cal afegir la superficie.']
        if not localitat:
            errors+=['Cal afegir la localitat']
        if not any:
            errors+=['Cal afegir un any.']

        if not errors:
            try:
                any = int(any)
            except Exception or ValueError:
                errors+=['L\'any no té un format correcte.']
            if any<0:
                errors+=['L\'any és negatiu.']
            try:
                superficie=float(superficie)
            except Exception or ValueError:
                errors+=['El valor indicat en la superfície no té un format correcte.']
        if errors:
            altresPuntsPerProcessar+=[puntNou]
            dict={}
            llista=[]
            i=0
            for punt in altresPuntsPerProcessar:
                puntSplit=punt.split(",")
                dict["punt"] = puntSplit[0]+","+puntSplit[1]
                i=i+1
                llista += [dict]
                dict={}
            midaLlista = int(midaLlistaString)
            punts = json.dumps(llista)
            return render(request, "puntsGeoGrafics/afegirNouPunt.html", {'provincies': provinciesMostrar,'categories': categoriesMostrar, 'poblacions': poblacionsMostrar,'punts': punts, 'errors':errors, 'lenLlista':midaLlista})
        else:
            puntSplit = puntNou.split(",") #tinc el nom del punt, q no el vull per a res[0] <-> lat lng [1]
            coordenades = puntSplit[1].split(" ") #lat[0] long[1] en format string
            latitud=float(coordenades[0])
            longitud=float(coordenades[1])
            actiu=False
            sLocalitat = localitat.split(' ')  #em ve: poblacio<espai>(comarca),<espai>provincia
            poblacio = sLocalitat[0]
            poblacio = localitzacio.objects.all().filter(ciutat=poblacio)[0]
            if llocActiu == "True":
                actiu=True
            nouPunt = puntInteres(latitud=latitud, longitud=longitud, actiu=actiu, superficie=superficie, localitat=poblacio)
            nouPunt.save()
            p = puntInteres.objects.all().filter(latitud=latitud, longitud=longitud)[0]
            categoria = categoriaLocal.objects.all().filter(categoria=tipus)[0]
            localNou = local(localitzacio=p, nomLocal=nomLocal, estat_conservacio=int(puntuacio), categoria=categoria, anyConstruccio=any, descripcio=descripcioLocal)
            localNou.save()
            dict = {}
            llista = []
            i = 0
            for punt in altresPuntsPerProcessar:
                puntSplit = punt.split(",")
                dict["punt"] = puntSplit[0] + "," + puntSplit[1]
                i = i + 1
                llista += [dict]
                dict = {}
            midaLlista = int(midaLlistaString)
            punts = json.dumps(llista)
            if len(altresPuntsPerProcessar) == 1:
                if altresPuntsPerProcessar[0].split(',')[0] == '--- Siusplau selecciona un punt ---':
                    return redirect("/v1/geoInfoSystem/map/")
            else:
                midaLlista = int(midaLlistaString)
                punts = json.dumps(llista)
                return render(request, "puntsGeoGrafics/afegirNouPunt.html", {'provincies':provinciesMostrar ,'categories': categoriesMostrar, 'poblacions':poblacionsMostrar, 'punts': punts, 'errors':[], 'lenLlista':midaLlista})
    return render(request, "puntsGeografics/afegirNouPunt.html", {'provincies':provinciesMostrar,'categories':categoriesMostrar, 'poblacions':poblacionsMostrar,'punts':[], 'errors':[], 'lenLlista':0})

"""
AIXO ES PERQ AIXI ES COMPROVA SI ÉS SUPERUSUARI, EN ALTRE CAS NO ENTRARA
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_superuser)
def score_reset(self,...):
    ...
"""