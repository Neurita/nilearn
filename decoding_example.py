### All the imports
import numpy as np
import pylab as pl
from scipy import signal
import nibabel as ni
from scikits.learn.svm import SVC
from scikits.learn.feature_selection import SelectKBest, f_classif
from scikits.learn.pipeline import Pipeline
from scikits.learn.cross_val import LeaveOneLabelOut, cross_val_score
from scikits.learn.feature_extraction.image import grid_to_graph
from  scikits.learn.externals.joblib.memory import Memory

mem = Memory('./')

from supervised_clustering import SupervisedClusteringClassifier

### Load data
y, session = np.loadtxt("attributes.txt").astype("int").T
X = ni.load("bold.nii.gz").get_data()
mask = ni.load("mask.nii.gz").get_data()
shape = X.shape

# Process the data in order to have a two-dimensional design matrix X of
# shape (nb_samples, nb_features).
X = X[mask!=0].T

# Detrend data on each session independently
for s in np.unique(session):
    X[session==s] = signal.detrend(X[session==s], axis=0)

# Remove volumes corresponding to rest
X = X[y<=2]
y = y[y<=2]
session = session[y<=2]

X, y, session = X[y!=0], y[y!=0], session[y!=0]
n_samples, n_features = X.shape
n_conditions = np.size(np.unique(y))


### Define the prediction function to be used.
# Here we use a Support Vector Classification, with a linear kernel and C=1
clf = SVC(kernel='linear', C=1.)

### Define the dimension reduction to be used.
# Here we use a classical univariate feature selection based on F-test,
# namely Anova. We set the number of features to be selected to 500
feature_selection = SelectKBest(f_classif, k=500)

### We combine the dimension reduction and the prediction function
anova_svc = Pipeline([('anova', feature_selection), ('svc', clf)])

### Define the cross-validation scheme used for validation.
# Here we use a LeaveOneLabelOut cross-validation on the session, which
# corresponds to a leave-one-session-out
session /= 5
cv = LeaveOneLabelOut(session)

### Compute the prediction accuracy for the different folds (i.e. session)
cv_scores = cross_val_score(anova_svc, X, y, cv=cv, n_jobs=-1,
                            verbose=1, iid=True)

### Return the corresponding mean prediction accuracy
classification_accuracy = np.sum(cv_scores) / float(n_samples)
print "=== ANOVA ==="
print "Classification accuracy: %f" % classification_accuracy, \
    " / Chance level: %f" % (1. / n_conditions)

### Same test using the supervised clustering
A =  grid_to_graph(n_x=shape[0], n_y=shape[1], n_z=shape[2], mask=mask)
sc = SupervisedClusteringClassifier(connectivity=A, n_jobs=8, n_iterations=100)
cv_scores = cross_val_score(sc, X, y, cv=cv, n_jobs=1,
                            verbose=1, iid=True)
classification_accuracy = np.sum(cv_scores) / float(n_samples)
print "=== SUPERVISED CLUSTERING ==="
print "Classification accuracy: %f" % classification_accuracy, \
    " / Chance level: %f" % (1. / n_conditions)
sc.fit(X, y)
print "Number of parcellations : %d" % len(sc.coef_)
pl.figure()
pl.subplot(2, 1, 1)
pl.plot(sc.scores_)
pl.title('scores')
pl.subplot(2, 1, 2)
pl.plot(sc.delta_scores_)
pl.title('delta')
pl.show()