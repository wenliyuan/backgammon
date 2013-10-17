import player
import numpy as np

def get_col_feats(column,color):
    feats = [0.]*3
    if len(column)>0 and column[0]==color:
        for i in range(len(column)):
            feats[min(i,2)] += 1
    feats[-1] = feats[-1]/2.0
    return feats
            
def extract_features(game):
    """
    @params game: state of backgammon board
    
    @returns features: list of real valued features
    """
    features = []
    for color in game.colors:
        for col in game.grid:
            feats = get_col_feats(col,color)
            features += feats
        features.append(float(len(game.bar_pieces[color]))/2)
        features.append(float(len(game.out_pieces[color]))/game.numpieces[color])
    return features

def nnEvaluate(game,weights):
    w1,w2,b1,b2 = weights
    features = np.array(extract_features(game)).reshape(-1,1)
    hiddenAct = 1/(1+np.exp(-(w1.dot(features)+b1)))
    score = 1/(1+np.exp(-(w2.dot(hiddenAct)+b2)))
    return score

def simpleEvaluate(game,color):
    numSingletons = 0
    for col in game.grid:
        if len(col)==1 and col[0]==color:
            numSingletons += 1

    score = 5.*len(game.out_pieces[color])
#    score -= 0.5*len(game.bar_pieces[color]) 
#    score -= 0.5*numSingletons
    return score

class TDPlayer(player.Player, object):
    
    def __init__(self,color,num,weights,gamma):
        super(self.__class__,self).__init__(color,num)
        self.w1,self.w2,self.b1,self.b2 = weights
        self.V = []
        self.grads = []
        self.gamma = gamma 

    def take_turn(self,moves,game):
        move = None
        bestScore = 0
        worstScore = 1
        for m in moves:
            
            # take the move
            tmpGame = game.clone()
            tmpGame.take_turn(m,self.color)

            # evaluate the state
            features = np.array(extract_features(tmpGame)).reshape(-1,1)
            hiddenAct = 1/(1+np.exp(-(self.w1.dot(features)+self.b1)))
            pred = 1/(1+np.exp(-(self.w2.dot(hiddenAct)+self.b2)))
            if pred<worstScore:
                worstScore = pred
            if pred>bestScore:
                move = m
                bestFeats = features.copy()
                bestAct = hiddenAct.copy()
                bestScore = pred.copy()
        print "Best,",bestScore
        print "Worts,",worstScore
        self.grads.append(self.backprop(bestFeats,bestAct,bestScore))
        self.V.append(bestScore)
        return move
        
    def backprop(self,a1,a2,v):
        del2 = v*(1-v)
        del1 = self.w2.T*del2*a2*(1-a2)
        return [del1*a1.T,del2*a2.T,del1,del2]

    def compute_update(self,outcome):
        # outcome is 1 if win, 0 otherwise
        self.V.append(outcome)
        updates = [np.zeros(self.w1.shape),np.zeros(self.w2.shape),
                   np.zeros(self.b1.shape),np.zeros(self.b2.shape)]
        gradsums = [np.zeros(self.w1.shape),np.zeros(self.w2.shape),
                   np.zeros(self.b1.shape),np.zeros(self.b2.shape)]

        for t in xrange(len(self.V)-1):
            currdiff = self.V[t+1]-self.V[t]
            for update,gradsum,grad in zip(updates,gradsums,self.grads[t]):
                gradsum += self.gamma*gradsum+grad
                update += currdiff*gradsum
        return updates
