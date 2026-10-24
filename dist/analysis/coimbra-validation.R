# Independent tabular checks and graphics; no external R packages.
x <- read.csv('dist/analysis/coimbra-historical-comparison.csv')
stopifnot(nrow(x)==10, all(x$q_daily_m3s>0), all(is.na(x$iou_diagnostic) | x$iou_diagnostic>=0 & x$iou_diagnostic<=1))
y <- x[x$duration_assumed_h==24,]
png('dist/figures/14_validacao_R.png',width=1500,height=850,res=145)
par(mar=c(7,5,5,2))
barplot(y$overbank_area_m2/10000,names.arg=y$event,col='#007c87',ylab='\u00c1rea fora do canal assumido (ha)',las=2,
        main='Reconstitui\u00e7\u00e3o explorat\u00f3ria com caudais m\u00e9dios di\u00e1rios',ylim=c(0,max(y$overbank_area_m2/10000)*1.15))
mtext('Dura\u00e7\u00e3o assumida: 24h. \u00c1reas totais do piloto, antes das exclus\u00f5es da compara\u00e7\u00e3o SAR.',side=3,line=.5,cex=.8)
mtext('N\u00e3o representa mancha hist\u00f3rica validada nem \u00e1rea efetivamente inundada.',side=1,line=5.5,cex=.8)
dev.off()
writeLines(capture.output(sessionInfo()),'dist/analysis/validation-R-sessionInfo.txt')
