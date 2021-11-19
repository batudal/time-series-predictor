import update
from keras.models import Sequential
from keras.layers import LSTM
from keras.layers import Dense
from numpy import array, hstack
import datetime
#import tensorflow as tf

def split_sequences(sequences, n_steps):
	X, y = list(), list()
	for i in range(len(sequences)):
		# find the end of this pattern
		end_ix = i + n_steps
		# check if we are beyond the dataset
		if end_ix > len(sequences):
			break
		# gather input and output parts of the pattern
		seq_x, seq_y = sequences[i:end_ix, :-1], sequences[end_ix-1, -1]
		X.append(seq_x)
		y.append(seq_y)
	return array(X), array(y)

def createStack():
    for m in update.metrics:
        print(m)
        sr = update.getIndicator(m)
        if m == update.metrics[0]:
            df = sr
            #print("first: {}".format(df))
        else:
            df = hstack((df,sr))
    df = df[1:,:]
    return df

def predict(n_steps=7, epochs=200):
	#prepare
	df = createStack()
	X, y = split_sequences(df, n_steps)
	n_features = X.shape[2]

	# define model
	model = Sequential()
	model.add(LSTM(50, activation='relu', input_shape=(n_steps, n_features)))
	model.add(Dense(1))
	model.compile(optimizer='adam', loss='mse')

	# log_dir = "logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
	# tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)
	
	# fit model
	model.fit(X, y, epochs=epochs, verbose=0)
	# demonstrate prediction
	x_input = array(df[-(n_steps):,:-1])
	#print(x_input.shape)
	#x_input = array([[80, 85], [90, 95], [100, 105]])
	x_input = x_input.reshape((1, n_steps, n_features))
	yhat = model.predict(x_input, verbose=0)
	print(yhat)
	return yhat

if __name__ == "__main__":
	predict()