#pragma once
#include <JuceHeader.h>
namespace CetusEQ {
enum FilterType : int { Bell=0, LowShelf=1, HighShelf=2, HighPass=3, LowPass=4, Notch=5 };
inline bool canProcessDynamics(int type) noexcept { return type==Bell || type==LowShelf || type==HighShelf; }
inline juce::dsp::IIR::Coefficients<float>::Ptr makeCoefficients(
        double sr,float hz,float q,float gainDb,int type) {
    using Coeff=juce::dsp::IIR::Coefficients<float>;
    const float f=juce::jlimit(20.0f,juce::jmax(20.1f,(float)sr*0.475f),hz);
    const float Q=juce::jlimit(0.2f,12.0f,q);
    const float g=juce::Decibels::decibelsToGain(gainDb);
    switch(type) {
        case LowShelf: return Coeff::makeLowShelf(sr,f,Q,g);
        case HighShelf:return Coeff::makeHighShelf(sr,f,Q,g);
        case HighPass: return Coeff::makeHighPass(sr,f,Q);
        case LowPass:  return Coeff::makeLowPass(sr,f,Q);
        case Notch:    return Coeff::makeNotch(sr,f,Q);
        default:       return Coeff::makePeakFilter(sr,f,Q,g);
    }
}
}
