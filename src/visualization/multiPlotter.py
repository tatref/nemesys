from typing import Dict, Tuple, List, Any

import numpy
import matplotlib.pyplot as plt

from visualization.plotter import MessagePlotter
from inference.segments import MessageSegment, TypedSegment, MessageAnalyzer
from netzob.Model.Vocabulary.Messages.AbstractMessage import AbstractMessage


class MultiMessagePlotter(MessagePlotter):
    """
    Different methods to plot data of many messages individually in one big figure.
    """
    from utils.loader import SpecimenLoader

    def __init__(self, specimens: SpecimenLoader, analysisTitle: str,
                 nrows: int, ncols: int,
                 isInteractive: bool=False):
        super().__init__(specimens, analysisTitle, isInteractive)
        self._fig, self._axes = plt.subplots(nrows=nrows, ncols=ncols)  # type: plt.Figure, numpy.ndarray
        if not isinstance(self._axes, numpy.ndarray):
            self._axes = numpy.array(self._axes)
        self._fig.set_size_inches(16, 9)


    def setFigureSize(self, w, h):
        self._fig.set_size_inches(w, h)


    def plotInEachAx(self, valuesList: List[List], linestyle:Dict[str, Any]=MessagePlotter.STYLE_MAINLINE,
                     xshift: int=None):
        """
        Plot each value sequence in the list to a separate subplot.

        :param valuesList: List of value-sequences to plot.
        :param linestyle: The line style as dict of keyword values for pyplot's plot function.
        :param xshift: If set, shift the plot in horizontal direction by this value
        """
        for ax, values in zip(self._axes.flat, valuesList):
            if xshift:
                xvalues = range(xshift, xshift + len(values))
                ax.plot(xvalues, values, **linestyle)
            else:
                ax.plot(values, **linestyle)
            ax.autoscale(tight=True)


    def scatterInEachAx(self, valuesList: List[Tuple[List, List]], marker='_'):
        """
        Scatter plot of the given values. Each pair of value-sequences is plotted into a separate subplot.

        :param valuesList: List of value-sequence pairs. First sequence are x-values, second y-values.
        :param marker: The marker to use in the plot.
        """
        for ax, values in zip(self._axes.flat, valuesList):
            ax.scatter(values[0], values[1], marker=marker, s=5)


    def fieldmarkersInEachAx(self, fieldEnds: List[List[int]]):
        """
        Plot vertical lines into each subplot at the given x-value.

        :param fieldEnds: Values to mark in each subplot.
        """
        for ax, fends in zip(self._axes.flat, fieldEnds):
            for fe in fends:
                ax.axvline(x=fe, **MessagePlotter.STYLE_FIELDENDLINE)
            ax.set_xticks(sorted(fends))


    def nameEachAx(self, labels: List[str]):
        """
        Title for each subplot.

        :param labels: List of strings to place beside each subplot.
        """
        for ax, title in zip(self._axes.flat, labels):
            ax.set_title(title, fontdict={'fontsize': 'x-small'})


    def plotSegmentsInEachAx(self, messagesInSegments: List[List[MessageSegment]]):
        """
        Plot each message to a separate subplot, while adding their constituting segments.

        :param messagesInSegments: Lists of segments for messages to plot in a subplot for each message.
        """
        linestyle = { 'linewidth': .2, 'alpha': .4 }
        for ax, segmentList in zip(self._axes.flat, messagesInSegments):
            analysisValues = segmentList[0].analyzer.values
            ax.plot(analysisValues, **MessagePlotter.STYLE_COMPARELINE)
            ax.set_xticks([segment.offset for segment in segmentList])
            for segment in segmentList:
                xshift = segment.offset
                try:
                    vallen = len(segment.values)
                    values = segment.values if segment.length == vallen \
                        else segment.values + [numpy.nan] * (segment.length - vallen)
                except TypeError:
                    lenextend = segment.length + 1 if xshift+segment.length < len(analysisValues) else segment.length
                    values = [segment.values] * lenextend
                    vallen = lenextend
                xvalues = range(xshift, xshift + vallen)
                ax.fill_between(xvalues, analysisValues[xshift : xshift+vallen],
                                values, alpha=.3)
                ax.plot(xvalues, values, **linestyle)
            ax.autoscale(tight=True)


    def plotSubfigs(self, analysisResults: List[List[float]], subfigName: List[str]=None,
                    compareValue: List[List[float]]=None, fieldEnds: List[List[int]]=None,
                    markextrema: bool=False,
                    resultsLabel: str=None, compareLabel: str=None, fieldEndMarks: bool=True):
        """
        Plot different aspects about analysis results.

        :param analysisResults: The results of a message analyzer for each message.
        :param subfigName: Titles for each subplot.
        :param compareValue: Values to plot for comparison for each message.
        :param fieldEnds: True field ends to plot for reference to each message.
        :param markextrema: If set, plot the local extrema of the analysis results.
        :param resultsLabel: Label for the results.
        :param compareLabel: Label for the compare values.
        :param fieldEndMarks: Mark the field ends with dots on the graph
        """

        # xshift=1  # shift to the right by one, since we want to see the value for x at position x+1
        self.plotInEachAx(analysisResults,
                          linestyle=MessagePlotter.STYLE_ALTMAINLINE \
                              if not resultsLabel else dict(MessagePlotter.STYLE_ALTMAINLINE,
                                                            label=resultsLabel)
                          )
        if markextrema:
            self.scatterInEachAx([MessageAnalyzer.localMinima(values) for values in analysisResults])
            self.scatterInEachAx([MessageAnalyzer.localMaxima(values) for values in analysisResults])

        if compareValue:
            self.plotInEachAx(compareValue,
                              linestyle=MessagePlotter.STYLE_COMPARELINE \
                                  if not compareLabel else dict(MessagePlotter.STYLE_COMPARELINE,
                                                                label=compareLabel)
                              )

        if fieldEnds:
            self.fieldmarkersInEachAx(fieldEnds)
            if fieldEndMarks:
                try:
                    self.scatterInEachAx(
                        [ (fe[:-1], [ar[endbyte] for endbyte in fe[:-1] ])
                          for fe, ar in zip(fieldEnds, analysisResults) ],
                        marker='.'
                    )
                except IndexError:
                    print('Error: Dissector field index and message are contradicting. Field ends could not be marked.\n'
                          'Check dissector and message.')

        if subfigName:
            self.nameEachAx(subfigName)

        if resultsLabel or compareLabel:
            plt.legend()

    # noinspection PyDefaultArgument
    def printMessageBytes(self, messages: List[AbstractMessage], fontdict={'size': 2}):
        for ax, message in zip(self._axes.flat, messages):  # type: plt.Axes, AbstractMessage
            ymin, ymax = ax.get_ylim()
            ypos = ymin + (ymax-ymin) * .05
            for idx, byt in enumerate(message.data):  # type: bytes
                ax.text(float(idx)+.2, ypos, "{:02x}".format(byt), fontdict=fontdict)

            xmin, xmax = ax.get_xlim()
            yposAbove = ymin + (ymax - ymin) * .1
            ax.text(xmin + .2, yposAbove, "Message:", fontdict=fontdict)


    def printValues(self, analysisResults: List[Tuple[List[float], List[float]]]):
        for ax, coord in zip(self._axes.flat, analysisResults):
            for x, y in zip(coord[0], coord[1]):
                ax.text(x, y, "{:0.3f}".format(y), fontdict={'size': 2})


    def plotCompareFill(self, analysisResults: List[List[float]], compareValues: List[List[float]]):
        """
        Fill the difference between analysisResults and compareValue in each plot.

        Call only after first plot into the figure has been done.

        :param analysisResults: The first list of analysis results
        :param compareValues: The second list of another analysis result
        """
        for ax, analysisResult, compareValue in zip(self._axes.flat, analysisResults, compareValues):
            MessagePlotter.fillDiffToCompare(ax, analysisResult, compareValue)


    def plotMultiSegmentLines(self, segmentGroups: List[Tuple[str, List[Tuple[str, TypedSegment]]]],
                              colorPerLabel=False):
        import matplotlib.cm

        # make the leftover axes invisible
        for ax in self._axes.flat:
            ax.axis('off')

        # SEgment GRoup for PLot
        for conlor, (ax, (title, segrpl)) in \
                enumerate(zip(self._axes.flat, segmentGroups)):  # type: (plt.Axes, List[Tuple[str, TypedSegment]])
            ax.set_title(title, fontdict={'fontsize': 'x-small'})
            ax.axis('on')

            if numpy.all([numpy.all(numpy.isnan(cseg.values)) for label, cseg in segrpl]):
                ax.text(0.5, 0.5, 'nan', fontdict={'size': 'xx-large'})
            else:
                unilabels = list({label for label, segment in segrpl})
                for label, segment in segrpl:
                    # noinspection PyUnresolvedReferences
                    ax.plot(segment.values, '.-', c=matplotlib.cm.tab20(
                            conlor if not colorPerLabel else unilabels.index(label)),
                        alpha=0.4, label=label)

                # deduplicate labels
                handles, labels = ax.get_legend_handles_labels()
                newLabels, newHandles = [], []
                for handle, label in zip(handles, labels):
                    if label not in newLabels:
                        newLabels.append(label)
                        newHandles.append(handle)
                ax.legend(newHandles, newLabels)

