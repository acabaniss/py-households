
"""A demographic agent-based model of individuals and households

This module implements an object-oriented, agent-based model of how individuals
live and die with empirical life tables and birth rates. It was originally
designed for historical and archaeological modelling, but can be used in a
variety of contexts. Demographic data are based on Bagnall and Frier.





"""

from households import np, rd, scipy, nx, plt, kinship, residency, behavior
"""Import the dependency packages defined in households.__init__.py

"""

print('Importing main.py')

global male, female
male, female = range(2)
"""int: integer values for men and women agents

Global variable used throughout the households package for legibility.
"""

class World:
    """The world of the simulation.
    
    This contains Community objects and will run the clock. Currently
    unimplmented.
    """
    
    def __init__(self):
        pass


class Community(object):
    """Communities are collections of people and houses following a schedule.
    
    community is both the storage for people living in houses and the container
    for the simulation that runs the schedule of the year.
    
    
    Parameters
    ----------
    pop : int
        The initial population of the simulation
    area : int
        The number of houses in the community
    startage : int
        The age at which all agents in the simulation start. Corrected for by burn-in.
    mortab : AgeTable
        An AgeTable storing a Coale and Demeny-style mortality schedule
    marrtab : AgeTable
        AgeTable storing marriage eligiblity probability by age and sex
    birthtab : AgeTable
        AgeTable storing probability of giving birth once married by sex (0 for men)
    locality : callable
        This defines the location newlyweds move to from behavior.locality, or a custom function.
    inheritance : callable
        This defines the inheritance system from behavior.inheritance, or a custom function.
    fragmentation : callable
        This defines the circumstances of houshold fissioning from behavior.fragmentation, or a custom function
        
        
    Attributes
    ---------
    year : int
        The year of the simulation of this community.
    area : int
        Number of houses in the community.
    population : int
        The current population of the community.
    housingcapacity : int
        The total housing capacity of the community in terms of people.
    births : int
        Total births this year.
    marriages : int
        Total marriages this year.
    deaths : int
        Total deaths this year.
    occupied : int
        Number of occupied houses.        
        
    houses : list of House objects
        The houses of the community.
    people : list of Person objects
        The people who currently live in the community.
    families : networkx DiGraph
        The network of kinship relations.
    
    mortab : AgeTable
        An AgeTable storing a mortality schedule for the community.
    marrtab : AgeTable
        An AgeTable storing marriage eligiblity probability by age and sex
    birthtab : AgeTable
        An AgeTable storing probability of giving birth once married by sex (0 for men)
    locality : callable
        This defines the location newlyweds move to from behavior.locality, or a custom function.
    inheritance : callable
        This defines the inheritance system from behavior.inheritance, or a custom function.
    fragmentation : callable
        This defines the circumstances of houshold fissioning from behavior.fragmentation, or a custom function
        
    thedead : list
        List of all dead agents, still required for genealogy.
    deathlist : list
        History of deaths per year.
    birthlist : list
        History of births per year.
    marriedlist : list
        History of number of marriages per year.
    poplist : list
        History of population by year.
    arealist : list
        History of number of houses per year.
    occupiedlist : list
        History of number of occupied houses per year.        
    """
    
    global male, female
    def __init__(self,pop,area,startage,mortab,marrtab,birthtab,locality,inheritance,fragmentation):
        
        self.year = 0
        
        # Create the houses
        self.area = area #The number of houses to create
        self.houses = []
        for i in xrange(area):
            self.houses.append(House(10,self)) #Create each house with a maximum number of people who can reside there
        self.housingcapacity = sum([i.maxpeople for i in self.houses])    
        
        # Generate the population
        self.population = pop #The number of individuals to start in the community
        # populate the community
        self.people = []
        for i in xrange(pop):
            self.people.append(person(rd.choice([male,female]),startage,self,None)) #Generate a new person with age startage
            #NB: currently a 50-50 sex ratio, should be customisable. Consider for expansion. 


        #Define dynamics of demography
        self.mortab = mortab # the death table for the community
        self.marrtab = marrtab #the probability of marriage at a given age by sex
        self.birthtab = birthtab #the probability of a woman giving birth at a given age if married
        self.locality = locality
        self.inheritance = inheritance
        self.fragmentation = fragmentation
        #Note: add an incest-rule option.
        #Note: add value checks.
        
        #Define a network to keep track of relations between agents
        self.families = nx.DiGraph()
        for individual in self.people:
            self.families.add_node(individual) 
        
        #Define statistics to keep track of each step
        self.deaths = 0
        self.births = 0
        self.occupied = 0 # Occupied houses
        self.marriages = 0
                
        #Define history of the statistics
        self.thedead = [] #store the list of dead agents
        self.deathlist = [self.deaths]
        self.birthlist = [self.births]
        self.poplist = [self.population]
        self.arealist = [self.area]
        self.occupiedlist = [self.occupied]
        self.marriedlist = [self.marriages]
        
    def progress(self):
        """Progress the community 1 time-step (year).
        
        The order of steps in the simulation follows this schedule:
            1) randomize the order of agents,
            2) death (and thereby inheritance),
            3) fragmentation,
            4) marriage (and thereby locality), 
            5) birth, and 
            6) recalculate all statistics and end the year.
        """
        
        #Step 1: randomize population order and reset statistics
        rd.shuffle(self.people)
        self.deaths = 0
        self.births = 0
        
        #Step 2: iterate through each person for death, marriage, and birth
        for x in self.people:
            x.die()
            
        #Remove the dead from the community
        remove = [i for i in range(len(self.people)) if self.people[i].dead == True]
        remove.reverse()
        for i in remove:
            self.thedead.append(self.people.pop(i))
            #This simultaneously adds a person to thedead and removes them from people
            self.deaths += 1
            
        #Check for household fragmentation
        for h in self.houses:
            self.fragmentation(h)
        
        #Go through the marriage routine for all agents
        for x in self.people:
            x.marriage()
            
        # Go through the birth routine for all agents
        for x in self.people:
            x.birth()
            
        #Recalculate statistics
        self.population = len(self.people)
        self.births = len([1 for x in self.people if x.age == 0])
        self.occupied = len([x for x in self.houses if x.people != []])
        self.deathlist.append(self.deaths)
        self.birthlist.append(self.births)
        self.poplist.append(self.population)
        self.arealist.append(self.area)
        self.occupiedlist.append(self.occupied)
        self.marriages = len([x for x in [x for x in self.people if x.married == True] if x.married_to.dead == False])
        self.marriedlist.append(self.marriages)
        
        self.year += 1

    def get_eligible(self,agent):
        """Returns list of all eligible marriage partners of the opposite sex.
        
        Searches through all 
        
        Parameters
        ----------
        
        """
        
        candidates = []
        relations = kinship.get_siblings(agent,self.families) 
        #Note at present that this only accounts for direct incest; a flexible
        ## incest rule would be a useful expansion here. 
        if relations == None: relations = []
        for x in self.people:
            if x.sex != agent.sex:
                #If unmarried and not a sibling
                if x.married == False and (x in relations) == False:
                    candidates.append(x)
        return candidates                    


class person(object):
    """An agent with a social structure and kinship.
    
    Create a new person in the community.
    
    Parameters
    ----------
    sex : {male,female}
        The sex of the agent assigned at creation.
    age : int
        Age of the individual assigned at creation, then aging regularly.
    mycomm : community
        The community to which this individual belongs.
    myhouse : house
        The house in which this individual resides.
    
    Attributes
    ----------
    sex : {male,female}
        The sex of the agent assigned at creation.
    age : int
        Age of the individual assigned at creation, then aging regularly.
    mycomm : community
        The community to which this individual belongs.
    myhouse : house
        The house in which this individual resides.
    dead : bool
        Records whether the person is dead or alive.
    married : {None, False, True}
        The marriage status of the individual.
            None - too young to be married;
            False - unmarried but eligible;
            True - married or widowed (the model does not allow remarriage)
    married_to : {None, person}
        The spouse of this individual.
    birthyear : int
        The year this individual was born.        
    """
    
    #Note: remarriage needs to be added as an option
    def __init__(self,sex,age,mycomm,myhouse):

        self.sex = sex
        self.age = age
        self.mycomm = mycomm #link to the community
        self.myhouse = myhouse #link to their house
        
        self.dead = False
        self.married = None #Variable to store marriage status; None because not elegible
        self.married_to = None #The individual to whom this individual is married
        
        self.birthyear = self.mycomm.year
        # Options for married include None (too young for marriage), False 
        ## (old enough but not eligible yet), or True (yes or widowed)
        
    def die(self):
        """Check whether this person dies or ages 1 year.
        
        Checks the community mortality table for this individual. If the individual
        lives, they age one year. Otherwise, they die, inheritance takes place, and
        the person is removed from the house.
        """
        
        #figure out if this person dies
        r = self.mycomm.mortab.get_rate(self.sex,self.age)
        if r <= rd.random(): #stay alive
            self.age += 1
        else: #if this person died this year, toggle them to be removed from the community
            self.dead = True
            self.mycomm.inheritance(self)
            if self.myhouse is not None:
                self.myhouse.remove_person(self)
        # Some inheritance rules need to happen here!
        #Note that at present this means that there is no update in the marriage
        ## state of the other person; this means people can only be married 
        ## once.
        
    def marriage(self):
        """Check whether this agent gets married this timestep.
        
        This step determines marriage eligibility, as well as finding potential
        candidates for marriage. At present the algorithm guarantees marriage
        if there are any eligible candidates of the opposite sex. 
        """
        
        if self.married == True: #if married, don't run this script
            pass 
        elif self.married == False: #if this agent is eligible to be married
            #get the list of eligible candidates for marriage
            candidates = self.mycomm.get_eligible(self)
            ##NOTE: evntually this must be adapted to get those not related to a given person by a certain distance
            if len(candidates) != 0: #if there are any eligible people
                choice = rd.choice(candidates) #Pick one
                # Set self as married
                self.married = True
                self.married_to = choice
                #Set the other person as married
                choice.married = True
                choice.married_to = self
                ## Add links to the network of families
                self.mycomm.families.add_edges_from( [(self,choice,{'type' : 'marriage'}),
                (choice,self,{'type' : 'marriage'})])
                ## Run the locality rules for this community
                husband, wife = (self,choice) if self.sex == male else (choice,self)
                self.mycomm.locality(husband,wife)
        else: #if none (== too young for marriage), check eligibility
            e = self.mycomm.marrtab.get_rate(self.sex,self.age)
            if rd.random() < e: #If eligibility possible, change staus
                self.married = False
    
    def birth(self):
        """Determine whether this agent gives birth.
        
        This relies on the fertility schedule in self.mycomm.birthtab to decide
        whether a married woman gives birth this year. If so, this method creates that 
        child in the same house.        
        """
        
        if self.sex == female and [self.married_to.dead if self.married == True else True][0] == False: #If married, husband is alive, and self is a woman
            b = self.mycomm.birthtab.get_rate(self.sex,self.age)
            if rd.random() < b: # if giving birth
                # Create a new child with age 0
                child = person(rd.choice([male,female]),0,self.mycomm,self.myhouse)
                self.mycomm.people.append(child) #add to the community
                self.myhouse.add_person(child)
                # Add the child to the family network
                self.mycomm.families.add_edge(self,child,{'type' : 'birth'})
                self.mycomm.families.add_edge(self.married_to,child,{'type' : 'birth'})

class house(object):
    """Creates a house in which persons reside.
    
    Parameters
    ----------
    maxpeople : int
        Maximum number of residents before the house is crowded. Currently no 
        repercussion for a crowded house.
    mycomm : community
        The community in which this house was built


    Attributes
    ----------
    maxpeople : int
        Maximum number of residents before the house is crowded. Currently no 
        repercussion for a crowded house.
    mycomm : community
        The community in which this house was built
    people : list
        List of the people who reside in the house.
    owner : person
        The person who owns this house. Assumes single or primary ownership.
    """
    
    #Houses belong to the community, have an owner, contain people
    #EVENTUALLY, houses may be expanded, change through time, etc. 
    def __init__(self,maxpeople,mycomm):
        self.maxpeople = maxpeople
        self.mycomm = mycomm
        self.people = []
        self.owner = None #pointer to the agent who owns the house
    
    def add_person(self,tobeadded):
        """Add a person to the house.
        
        Parameters
        ---------
        tobeadded : person
            The person to be added to the residents of the house.
        """
        self.people.append(tobeadded)
    
    def remove_person(self,toberemoved):
        """Remove a person from the house.
        
        Parameters
        ---------
        toberemoved : person
            The person to be removed from the residents of the house
        """
        self.people.remove(toberemoved)
        

class AgeTable(object):
    """AgeTables store age-specific annual rates of death, marriage, birth, etc.
    
    AgeTables create a schedule of age- and sex- dependent annual rates of 
    different phenomena, literally anything from marriage eligibility to death.
    
    Parameters
    ----------
    ages : list
        A list of ages including the lower bounds, such that ages[0] <= x < ages[1] is the comparison.
    sex1, sex2 : {male, female}
        The variables defining which rates correspond to which sex.
    rates1, rates2 : list
        Annual chance of occurence for each interval. n.b. that len(rates) - len(ages) - 1
    
    Attributes
    ----------
    
    
    """
    global male, female

    def __init__(self,ages,sex1,rates1,sex2,rates2):
        self.ages = ages
        self.sex1 = sex1
        self.rates1 = rates1
        self.sex2 = sex2
        self.rates2 = rates2  
        
    def get_rate(self,sex,age):
        """Returns the annual rate for a given sex and age.

        Parameters
        ----------
        sex : {male, female}
            The sex in the table to be consulted.
        age : int
            The age of the individual. Must be within defined range of table
 
        Returns
        -------
        float
            The rate for that age and sex.
            
        """
        i = [i for i in range(len(self.ages)-1) if age>=self.ages[i] and 
        age<self.ages[i+1]][0]
        if sex == self.sex1:
            return self.rates1[i]
        else:
            return self.rates2[i]

##Example code
if __name__ == '__main__':
    #Life tables are Coale and Demeny: Male, west 4, female west 2, .2% annual increase. See Bagnall and frier
    maledeath = pd.read_csv('../data/demo/West4Male.csv')
    ages = list(maledeath.Age1) + [list(maledeath.Age2)[-1]]
    malerates = list(maledeath[maledeath.columns[2]])
    femaledeath = pd.read_csv('../data/demo/West2Female.csv')
    femalerates = list(femaledeath[femaledeath.columns[2]])
    bagnallfrier = households.AgeTable([0,1] + range(5,105,5), male, malerates, female, femalerates)
    del maledeath, femaledeath
    
    examplebirth = AgeTable([0,12,40,50,100],female,[0,.3,.1,0],male,[0,0,0,0,0])
    
    examplemarriage = AgeTable([0,12,17,100],female,[0,1./7.5,1./7.5],male,[0,0,0.0866]) #These values based on Bagnall and Frier, 113-4 (women) and 116 (men) for Roman egypt
    
    def inheritance_moderate(agent):
        """
        Upon the death of the patriarch, the house is given to someone in this
        order:
            
        Male children in order of age
        Children of brothers not in line for succession (have to move into household)
        
        This stems from the description of the moderate inheritance regime in Asheri
        """
        #The moderate inheritance regime of Asheri 1963
        # Check if patriarch
        if agent.sex == male and any([h.owner == agent for h in agent.comm.houses]):
            #First priority: male children
            inherited = bhv.inheritance.inherit_sons(agent,True) #what about grandchildren?
            if inherited == False:
                #Second priority: adoption of brothers' younger sons
                inherited = bhv.inheritance.inherit_brothers_sons(agent)
                if inherited == False:
                    #If there is still no heir, for now the ownership defaults
                    bhv.inheritance.inherit(agent,None)    
    def brother_loses_out_15(house):
        if house.people != [] and house.owner != None:
            bhv.fragmentation.brother_loses_out(house,15)
                
    #An example of a single basic run
    testcase = community(500,500,12,bagnallfrier,examplemarriage,examplebirth,bhv.locality.patrilocality,inheritance_moderate,brother_loses_out_15)
    houstory = {}
    for h in testcase.houses:
        houstory[h] = {'classify' : [],'pop' : []}
    for i in xrange(200):
        testcase.progress()
        for h in testcase.houses:
            houstory[h]['classify'].append(residency.classify_household(h))
            houstory[h]['pop'].append(len(h.people))
    plt.plot(testcase.poplist)
    
    #Plot the changing types of houses
    array = []
    labels = ['empty','solitary','no-family','nuclear','extended','multiple']
    which = lambda x: [i for i in xrange(len(labels)) if labels[i] == x][0]
    for y in xrange(testcase.year):
        new = [0.]*6
        for k in houstory.keys():
            w = which(houstory[k]['classify'][y])
            new[w]+=1
        new = [x*1./sum(new[1:]) for x in new[1:]]       
        array.append(new)
    plt.stackplot(range(testcase.year),np.transpose(array),baseline='zero')
    plt.axis([0,300,0,1])
    
    #An example of a repetition script
    record = []
    repeat = 50
    years=200
    for r in xrange(repeat):
        rd.seed()
        testcase = community(500,500,12,west2male,examplemarriage,examplebirth,bhv.locality.patrilocality,inheritance_moderate,brother_loses_out_15)
        houstory = {}
        for h in testcase.houses:
            houstory[h] = []
        for i in xrange(years):
            testcase.progress()
            for h in testcase.houses:
                houstory[h].append(classify_household(h))
        record.append(testcase.poplist)
    
    for i in record:
        plot(i)
    
    window = 20
    meancorr = []
    for y in xrange(years-window):
        count = 0
        meancorr.append(0.)
        for i in xrange(repeat):
            for j in xrange(i):
                if j != i:
                    meancorr[y] += corrcoef([record[i][x] for x in range(y,y+window)],[record[j][x] for x in range(y,y+window)])[0][1]
                    count +=1
        meancorr[y] = meancorr[y]/count
        
                    
    
    
        
        
        
        owner_dead = [h for h in [h for h in testcase.houses if h.owner is not None] if h.owner.dead == True]
        if len(owner_dead) > 0:
            print('Something has gone wrong')
            break
    plot_classify(testcase.houses)
    
    df = pd.DataFrame({'classify' : [classify_household(h) for h in testcase.houses if len(h.people)>0], 'size' : [len(h.people) for h in testcase.houses if len(h.people)>0]})
    groups = df.groupby('classify')
    groups.mean()
    


