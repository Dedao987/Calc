# -*- coding: cp1252 -*-
#
#  In Deze file zit de recept formule verwerkt.
#  de recept formule gaat als volgt te werk:

'''  

1. Bereken mix ratio's die zijn initieel natuurlijk 0   (alle subtotalen zijn 0 en dus ook grand total ) Calc_mix_ratios()
2. in Get_Max_deviation() wordt de maximale afwijking bepaald.
3. Vervolgens met Generate_place_advise wordt een lijst gemaakt met te zetten dozen.
   Als er nog niets geplaatst is dan is het hoogste BlendPercentage de hoogste afwijking.
   Daarom wordt de doos met de hoogste blend percentage als eerste aangeboden

   In geval rekenvoorbeeld Erik is dat  ['lotnr104', 'lotnr105', 'lotnr106']   (20%)

4. Met Place_Box(    Keuze   )  wordt er dan dus een bepaald gewicht toegevoegd.
5. Een nieuw Hoofd totaal wordt berekend met calc_grandtotal()

Nu terug naar stap 1 maar rekenen met het nieuwe grand totaal '''


#  Ook worden hier tijdens de sessie de formule variabelen bijgewerkt /'onthouden'
#  De recept subtotaal gewichten bijv.   self.Type1ATotal      (KG) (al toegevoegd aantal KG van dat recept deel)
#  De Mix ratio's in percentage  bijv.   self.Type1AMix        (%)
#  De afwijkingen in percentage  bijv.   self.Type1ADeviation  (%)
#  Grand total:  self.grandtotal                               (KG)
#  self.nrofmanualinputs  (aantal handmatige invoeren)
#  Aantal  auto bc scans
#  self.lastplacedbox     (laatst geplaatste doos)

 
import os
currdir = os.getcwd()


class recipe_formula():

    def __init__(self):

        #  Hier een voorbeeld van hoe het werkrecept is definieert.  (nog zonder SQLbatchname,rec name ect)
        '''recipeexample = {"('Type1A', 0)": {"100":
                                    {"Barcode1": "501",
                                     "Barcode2": "11919",
                                     "Barcode3": "3400",
                                     "NBunits": 718.0,
                                     "Unitweight": 220.0} ,
                    "BlendPercentage": 10.01, "line": "Stelen"},


                   "('Type1B', 10)": {"101":
                                    {"Barcode1": "5331",
                                     "Barcode2": "1181132419",
                                     "Barcode3": "3400",
                                     "NBunits": 707.0,
                                     "Unitweight": 211.5} ,
                    "BlendPercentage": 89.99, "line": "Dust"}, }'''

        # Je ziet de dictionairy recipeexample is een dictionairy die bestaat uit de hoofd keys:
        # *     "('Type1A', 0)"  
        # *     "('Type1B', 10)"
        # Deze hoofd keys zijn tuples bestaande uit recept ingredient en row positie ,(uit grid tabel)
        # het oproepen van deze hoofdkey geeft keys:
        # *     'BlendPercentage'
        # *     'line'
        # * en weer een key wat een dictionairy is met lotnrs, per lotnr heb je dan een dict met keys
        # * Barcode1
        # * Barcode2
        # * Barcode3
        # * NBunits
        # * unitweight

        # Het is dus een nested dict (dict met dict keys)


        #self.set_recipe_formula_globals(recipe)  Nee gebeurd via frame
        self.batchname = ''
        self.grandtotal       = 0
        self.nrofbcscans      = 0  # aantal barcode scans
        self.nrofkbscans      = 0  # aantal keyboard scans
        self.nrofmouseinputs  = 0  # aantal mouse invoer (drukknop)
        self.lastplacedbox    = ''
        self.misplacedboxesnr = 0 # misplaatste dozen

        self.nrofhakselplaced  = 0
        self.nroftoploadplaced = 0

        self.HakselTotal  = 0  # gewicht
        self.ToploadTotal = 0  # gewicht
        self.totalnrofplacedboxes = 0
        self.nrofplacedboxesDust = 0
        self.nrofplacedboxesStelen = 0


        

        # De init mag maar 1x worden aangeroepen (bij prog start) ,  bij recept wijziging NIET de class opnieuw instancieren!!
        # Als men toch wil schoon starten, roep reset_recipe_formula_globals aan!


    def wfloat(self,data):
        data = str(data).strip(' ').strip('%').strip('\r').strip('\n').replace(' ','').replace(',','.')
        try:
            returndata = float(data)
        except Exception:
            #print 'debug...  function wfloat in calc.py was given a param that could not be converted to float: ',repr(data),  ' function returned 0.0'
            returndata = 0.0
            #print 'data ',repr(data)
        return returndata

    def reset_recipe_formula_globals(self,recipe):
        # Voor als je tijdens of na een sessie wil schoon herstarten.
        # recipe wordt in dit geval allen gebruikt om te kunnen iteren.
        # En dan tijdens iteren de resets doen.
        # Bij start batch wordt deze aangeroepen.

        #raw_input('reset called')

        self.grandtotal = 0

        setattr(self,'grandtotal',0)
        setattr(self,'nrofbcscans',0)
        setattr(self,'nrofkbscans',0)
        setattr(self,'nrofmouseinputs',0)
        setattr(self,'nrofmanualinputs',0)
        setattr(self,'lastplacedbox','')
        setattr(self,'misplacedboxesnr',0)

        # haksel/topload process values reset...
        setattr(self,'nrofhakselplaced',0)
        setattr(self,'nroftoploadplaced',0)
        setattr(self,'HakselTotal',0)
        setattr(self,'ToploadTotal',0)

        setattr(self,'totalnrofplacedboxes'  , 0)
        setattr(self,'nrofplacedboxesDust'   , 0)
        setattr(self,'nrofplacedboxesStelen' , 0)
        
        
        for Ttype,v in recipe.iteritems():
            # process waarden resetten...
            if type(Ttype) is tuple:  # de meeste zijn tuple, 1 key is de recept naam, daar geen setattr voor doen.
                setattr(self,Ttype[0]+'Mix',0)
                setattr(self,Ttype[0]+'Deviation',0)
                setattr(self,Ttype[0]+'Total',0)
                # Blend is een vaste (wordt altijd uit recept gebr) , hierboven dus de process waarden

                # geplaatste dozen resetten:
                for key in v:
                    #if 'lotnr'in key:
                    if type(v[key]) is dict: # manier om doosnr/lotnr af te vangen. alleen dict keys zijn doos nr.
                        setattr(self,key,int(v[key]['NBunits']))
                        #print 'key  ',v[key]['NBunits']
                        #raw_input('dd')


        return True


    def set_recipe_formula_globals(self,recipe):

        #  Probeert eerst of de waarde al bestaat.  
        #  Als deze niet bestaat is het de eerste keer dat de app start.  De var wordt dan gedeclareerd met een initiele waarde.
        #  Als deze wel bestaat, moet de waarde onveranderd blijven.
        #  Als deze functie wordt aangeroepen bij het laden van een ander recept in dezelfde sessie dan worden dus 
        #  alleen potentioneel nieuwe waarden toegevoegd.

        for Ttype in recipe.keys():   

            if type(Ttype) is tuple:  
                try:
                    existingval = getattr(self,Ttype[0]+'Total')
                    #  dit definieert dus bijvoorbeeld self.Type1ATotal  waarde initieel  int 0   als Ttype Type1a heet
                except AttributeError:
                    #setattr(self,Ttype[0]+'Total',0)  #  global var declr. for sub Totals
                    setattr(self,Ttype[0]+'Total',0)  #  global var declr. for sub Totals
            #else:
            #    print 'r name in set_recipe_formula_globals:  ',repr(Ttype)


        # Mix ratios

        for Ttype in recipe.keys():
            if type(Ttype) is tuple:   # de juiste key voor de settattr
                try:
                    #existingval = getattr(self,Ttype+'Mix')
                    existingval = getattr(self,Ttype[0]+'Mix')
                except AttributeError:
                    #setattr(self,Ttype+'Mix',0)  #  global var declr. for Mix ratios
                    setattr(self,Ttype[0]+'Mix',0)  #  global var declr. for Mix ratios
            #else:
            #    print 'r name in set_recipe_formula_globals a:  ',repr(Ttype)

        # (Initial) Deviation percentages

        for Ttype in recipe.keys():
            if type(Ttype) is tuple:
                
                try:
                    #existingval = getattr(self,Ttype+'Deviation')
                    existingval = getattr(self,Ttype[0]+'Deviation')
                except AttributeError:
                    #setattr(self,Ttype+'Deviation',recipe[Ttype]['BlendPercentage'])  #  global var declr. for Deviations
                    setattr(self,Ttype[0]+'Deviation',recipe[Ttype]['BlendPercentage'])  #  global var declr. for Deviations
            #else:
            #    print 'r name in set_recipe_formula_globals b:  ',repr(Ttype)
            

        # nr of Boxes placed

        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:   
                for key in v:
                    if type(v[key]) is dict:
                        try:
                            getattr(self,key)
                        except AttributeError:
                            print ''
                            setattr(self,key,int(v[key]['NBunits']))
            #else:
            #    print 'r name in set_recipe_formula_globals c:  ',repr(Ttype)

        return True



    def calc_grandtotal(self,recipe):


        grandtotal = 0  #  function global

        for Ttype in recipe.keys():
            if type(Ttype) is tuple:
                a = self.wfloat(getattr(self,Ttype[0]+'Total'))
                grandtotal += self.wfloat(getattr(self,Ttype[0]+'Total'))
                #print 'grandtotal:' + str(grandtotal) + 'a: ' + str(a)
            #else:
            #    print 'not tuple in calc_grandtotal ',repr(Ttype)

        setattr(self,'grandtotal',grandtotal)  #  global set
        self.grandtotal = grandtotal
        return grandtotal


    '''def calc_line_total(self,recipe,reqline):
        # bereken de lijn totalen
        # kijk naar de

        dusttotal   = 0
        stelentotal = 0
        
        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                if 'dust' in v['line'].lower():
                    dusttotal += getattr(self,Ttype[0]+'Total')
                elif 'stelen' in v['line'].lower():
                    stelentotal += getattr(self,Ttype[0]+'Total')

        ltotdict    = {'dust':dusttotal,'stelen':stelentotal}
        return ltotdict[reqline]'''
        


    def Calc_mix_ratios(self,recipe):

        for Ttype,v in recipe.iteritems():

            if type(Ttype) is tuple:
                currsubtotal = getattr(self,Ttype[0]+'Total')  # huidig subtotal ophalen

                try: 
                    currmixratio = self.wfloat(currsubtotal) / self.wfloat(getattr(self,'grandtotal')) * 100.000
                    setattr(self,Ttype[0]+'Mix',currmixratio)
                    #print Ttype, 'Mix' , currmixratio , ' %'
                except Exception:
                    #print 'exception: ',Ttype
                    currmixratio = 0.00
            #else:
            #    print 'not tuple in calc_mix_ratios ',repr(Ttype)

        #print 'new mix ratios determined'
        return True
                

    
    def Get_Max_deviation(self,recipe):
        # nieuwe deviations berekenen (blend percentage - ratio percentage)
        #print 'recipe in dev: ',recipe
        deviationlist = []

        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                #print 'Ttype ',Ttype[0]
                dev = self.wfloat(v['BlendPercentage'])  -  self.wfloat(getattr(self,Ttype[0]+'Mix'))
                setattr(self,Ttype[0]+'Deviation',dev)
                #print 'rer dev',repr(dev)
                deviationlist.append(dev)
                deviationlist.sort()
            #else:
                #print 'not tuple in max_dev ',repr(Ttype)

        #print 'max deviation determined: ',max(deviationlist)
        return max(deviationlist)
            



    def Generate_place_advise(self,maxdev,recipe):
        # First find max deviation
        #maxdev = self.Get_Max_deviation(recipe)
        # Now use that percentage to find what to add
        choicelist = []

        #print 'recipe: ',recipe
        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                #print 'Ttype:' ,Ttype,'dev: ', getattr(self,str(Ttype)+'Deviation')
                if maxdev == getattr(self,Ttype[0]+'Deviation'):
                    #print 'yes!   Ttype: ',Ttype
                    for key,value in v.iteritems():
                        #print 'kie , val ',key , value, type(value)
                        #if 'lotnr' in key:
                        if type(value) is dict:  # betere manier om doosnr/lotnr af te vangen.  zo issie niet afhankelijk van prefix
                            choicelist.append(key.strip('\r\n'))
                            choicelist.sort()
                            line = v['line']
                            
                    return {'Ttype':Ttype[0],'choicelist':choicelist,'line':line}
            #else:
            #    print 'ELSE in generate_place_adv',repr(Ttype)


    def Place_Box(self,lotnr,recipe,decrement):

        if not lotnr == '':
            if self.check_if_lotnr_in_recipe(lotnr,recipe):

                print 'placing ',lotnr
                
                recipepart = self.get_recipepart_from_lotnr(lotnr,recipe)
                self.lastplacedbox = lotnr.strip('\r\n')
                # Find out the type and weight of the box...

                
                #print recipe[recipepart]
                lineforthisbox = recipe[recipepart]['line'].lower()
                
                Unitweight = recipe[recipepart][lotnr]['Unitweight']  # Unitweight uit recept data
                if decrement:
                    recipe[recipepart][lotnr]['NBunits'] -= 1
                currval = getattr(self,recipepart[0]+'Total')  # huidig subtotal ophalen
                Unitweighttoadd = self.wfloat(currval) + self.wfloat(Unitweight)       # Unitweight toevoegen aan subtotal
                setattr(self, recipepart[0]+'Total' , Unitweighttoadd)   # subtotal zetten. 
                #curboxesplaced = getattr(self,lotnr)   # dit incrementeerd het lotnr zelf
                #setattr(self,lotnr,recipe[recipepart][lotnr]['NBunits'])

                # Nu de stelen,dust, en totalen bijwerken  (per lijn en totaal)
                self.totalnrofplacedboxes += 1

                if 'stelen' in lineforthisbox:
                    self.nrofplacedboxesStelen += 1
                    #if not self.firstsevendone:
                        #self.firstsevenstemboxes.append(lotnr)
                        #self.boxesdict['batchname'] = self.batchname
                        #self.boxesdict['firstsevenstem'].append(lotnr)
                        
                        
                elif 'dust' in lineforthisbox:
                    self.nrofplacedboxesDust += 1

                return recipe
            else:
                print 'lot not in recipe',lotnr
                
            


    def get_recipepart_from_lotnr(self,lotnr,recipe):
        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                for key,value in v.iteritems():
                    if type(value) is dict:
                        if key == lotnr:                            
                            return Ttype
        return ' '
                    

    def check_if_lotnr_in_recipe(self,lotnr,recipe):
        
        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                for key,value in v.iteritems():
                    if type(value) is dict:
                        if key == lotnr:
                            return True
        return False

    def get_line_for_box(self,lotnr,recipe):
        for Ttype,v in recipe.iteritems():
            if type(Ttype) is tuple:
                for key,value in v.iteritems():
                    if type(value) is dict:
                        if key == lotnr:
                            return v['line']
        #print 'lotnr not found in recipe',lotnr
        return False
        
        


class HakselTopload(recipe_formula):

    def __init__(self):

        print ' '


    def calc_amount(self,grandtotal,percentage):
        onepercent = grandtotal/100.0
        return self.wfloat(onepercent) * self.wfloat(percentage)
    

    def get_boxes_needed(self,amount,boxweight):
        #print 'get boxes needed: ',amount,' delen door ',boxweight
        return self.wfloat(amount) / self.wfloat(boxweight)
    
    

    def calc_boxes_to_go(self,boxestoplace,boxesplaced):
        return self.wfloat(boxestoplace) - self.wfloat(boxesplaced)

    

#   Gebruik dit stuk om formula testing te doen: 
#   comment als je klaar bent en alles werkt.

# start comment hier...
'''from RecipeFileManagement import recipe_file_management
recipefilehandler = recipe_file_management()

testrecipe = recipefilehandler.get_recipe(filePath=currdir+'\\recipe\\testrecipe.dat')

gd = recipe_formula_class(recipe=testrecipe)


while 1:

    print '\nStart \n'
    
    print '\n=== Nieuwe mix ratios bepaald: === \n\n'   ,gd.Calc_mix_ratios(recipe=testrecipe)

    print '\n===  Maximale afwijking is nu: ===  \n'

    choice = 'lotnr' + str(raw_input('\nKies uit die volgende dozen (alleen nr)  %s  :'%gd.Generate_place_advise(recipe=testrecipe)['choicelist']))

    gd.Place_Box(lotnr=choice,recipe=testrecipe)

    print '\n=== Plaatsen van doos: ===  ',choice

    print '\n=== Totaal gewicht: ===  ' , gd.calc_grandtotal(recipe=testrecipe)'''




    


    

