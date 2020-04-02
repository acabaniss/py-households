"""Household fragmentation processes.

These functions are run by households each year to decide whether the household
needs to split apart into new households. This is to model conflicts such as
brother-brother conflicts after the death of the patriarch.

Each fragmentation function will need to take a household and determine 
whether anyone in that household needs to leave. If they do, move them.

"""

from households import np, rd, scipy, nx, plt, kinship, residency, behavior

print('importing fragmentation')

#import kinship as kn
#import inheritance as ih 
#import locality as lc

global male, female
male, female = range(2)
"""int: integer values for men and women agents

Global variable used throughout the households package for legibility.
"""

def no_fragmentation(house):
    """No fragmentation rule.
    
    A household with this rule will never fragment.
    
    Parameters
    ---------
    house : house
        The household which won't fragment.
    """
    pass

def brother_loses_out(house,age):
    """Non-owner adult brothers leave when the oldest brother inherits the house. 
    
    A (younger) adult brother who just lost out on the family inheritance leaves the
    house along with his family. Otherwise, everyone stays put.
    
    Parameters
    ---------
    house : house
        The household to check to see if it will fragment.
    age : int
        The age of majority (marriage often) for determining whether an adult 
        brother feels the pressure to leave and create a new household.
    """
    # Check whether any brothers are there
    if house.people != [] and house.owner != None:    
        siblings = kinship.get_siblings(house.owner,house.mycomm.families)
        if siblings != None:
            siblings = [x for x in siblings if x.sex == male and x.age >= age and x.dead == False]
            if len(siblings) > 0:
                for s in siblings:
                    #For each brother who lives in the house
                    if s in house.people:
                        #If there is another brother over the age of majority who is
                        ## not hte ownerwho lives there that person ( and their family)
                        ## moves out
                        # Pick a new house
                        new_house = behavior.locality.get_empty_house(house.mycomm.houses)
                        if new_house != None:
                            # Identify their family and move them
                            behavior.inheritance.move_family(s,new_house)
                        else:
                            # There is no new house, so stay put.
                            pass               

def house_gets_crowded(house):
    """Over-capacity housing prompts families to relocate.
    
    A house that exceeds its capacity gets rid of 1) non-kin of the owner,
    2) more distant kin of the owner.
    
    Parameters
    ---------
    house : house
        The house to check for overcrowding.
    """
    pass #To be continued